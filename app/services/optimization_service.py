import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Tuple, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import hyperopt
from hyperopt import fmin, tpe, hp, STATUS_OK, Trials
import threading
import copy

from app.database.repository.strategies import StrategyRepository
from app.database.repository.assets import AssetRepository
from app.services.data_service import DataService
from app.core.config import get_settings

# Set up logger
logger = logging.getLogger(__name__)

# Global optimization status storage
optimization_tasks = {}
optimization_tasks_lock = threading.Lock()

class OptimizationService:
    """
    Service for optimizing trading strategies
    """
    
    def __init__(self):
        """Initialize the optimization service"""
        self.settings = get_settings()
        self.data_service = DataService()
        
        # Default parameters for indicators
        self.default_params = {
            'percent_increase_buy': 0.02,
            'percent_decrease_sell': 0.02,
            'sell_down_lim': 2.0,
            'sell_rolling_std': 20,
            'buy_up_lim': -2.0,
            'buy_rolling_std': 20,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'rsi_period': 14,
            'stochastic_k_period': 14,
            'stochastic_d_period': 3,
            'fractal_window': 100,
            'fractal_lags': [10, 20, 40],
            'reactivity': 1.0,
            'weights': {
                'weekly_macd_weight': 0.25,
                'weekly_rsi_weight': 0.25,
                'weekly_stoch_weight': 0.25,
                'weekly_complexity_weight': 0.25,
                'macd_weight': 0.4,
                'rsi_weight': 0.3,
                'stoch_weight': 0.2,
                'complexity_weight': 0.1
            }
        }
        
        # Parameter search space for hyperopt
        self.param_space = {
            'percent_increase_buy': hp.uniform('percent_increase_buy', 0.01, 0.05),
            'percent_decrease_sell': hp.uniform('percent_decrease_sell', 0.01, 0.05),
            'sell_down_lim': hp.uniform('sell_down_lim', 1.0, 3.0),
            'sell_rolling_std': hp.quniform('sell_rolling_std', 10, 50, 5),
            'buy_up_lim': hp.uniform('buy_up_lim', -3.0, -1.0),
            'buy_rolling_std': hp.quniform('buy_rolling_std', 10, 50, 5),
            'macd_fast': hp.quniform('macd_fast', 8, 16, 1),
            'macd_slow': hp.quniform('macd_slow', 20, 30, 1),
            'macd_signal': hp.quniform('macd_signal', 7, 12, 1),
            'rsi_period': hp.quniform('rsi_period', 10, 20, 1),
            'stochastic_k_period': hp.quniform('stochastic_k_period', 10, 20, 1),
            'stochastic_d_period': hp.quniform('stochastic_d_period', 2, 5, 1),
            'fractal_window': hp.choice('fractal_window', [50, 100, 150, 200]),
            'reactivity': hp.uniform('reactivity', 0.8, 1.2),
            'weights_index': hp.choice('weights_index', [
                {
                    'weekly_macd_weight': 0.25,
                    'weekly_rsi_weight': 0.25,
                    'weekly_stoch_weight': 0.25,
                    'weekly_complexity_weight': 0.25,
                    'macd_weight': 0.4,
                    'rsi_weight': 0.3,
                    'stoch_weight': 0.2,
                    'complexity_weight': 0.1
                },
                {
                    'weekly_macd_weight': 0.2,
                    'weekly_rsi_weight': 0.4,
                    'weekly_stoch_weight': 0.2,
                    'weekly_complexity_weight': 0.2,
                    'macd_weight': 0.3,
                    'rsi_weight': 0.4,
                    'stoch_weight': 0.2,
                    'complexity_weight': 0.1
                },
                {
                    'weekly_macd_weight': 0.3,
                    'weekly_rsi_weight': 0.2,
                    'weekly_stoch_weight': 0.3,
                    'weekly_complexity_weight': 0.2,
                    'macd_weight': 0.2,
                    'rsi_weight': 0.3,
                    'stoch_weight': 0.4,
                    'complexity_weight': 0.1
                }
            ])
        }
    
    def run_optimization(self, db: Session, strategy_id: int, asset_ids: List[int], 
                        parameters: Dict[str, Any] = None, objective: str = "sharpe_ratio", 
                        days: int = 30, task_id: str = None) -> Dict[str, Any]:
        """
        Run optimization for a strategy with hyperopt
        
        Args:
            db: Database session
            strategy_id: Strategy ID to optimize
            asset_ids: List of asset IDs to include in optimization
            parameters: Optional parameter constraints
            objective: Objective function to maximize ('sharpe_ratio', 'total_return', etc.)
            days: Number of days of data to use for optimization
            task_id: Optional task ID for tracking status
            
        Returns:
            Optimization results
        """
        # Set task status to running
        if task_id:
            self._update_task_status(task_id, {
                'strategy_id': strategy_id,
                'status': 'running',
                'progress': 0.0,
                'started_at': datetime.utcnow(),
                'finished_at': None,
                'error': None
            })
        
        try:
            # Get strategy from database
            db_strategy = StrategyRepository.get_strategy(db, strategy_id=strategy_id)
            if not db_strategy:
                raise ValueError(f"Strategy with ID {strategy_id} not found")
            
            # Get assets from database
            assets = []
            for asset_id in asset_ids:
                db_asset = AssetRepository.get_asset(db, asset_id=asset_id)
                if db_asset:
                    assets.append(db_asset)
            
            if not assets:
                raise ValueError(f"No valid assets found for optimization")
            
            # Fetch market data for all assets
            market_data = self.data_service.get_market_data_for_assets(db, asset_ids, days=days)
            
            if not market_data:
                raise ValueError(f"No market data available for optimization")
            
            # Create base parameters by merging default with any provided constraints
            base_params = copy.deepcopy(self.default_params)
            if parameters:
                base_params.update(parameters)
            
            # Create parameter space for hyperopt
            space = {}
            for param_name, param_value in self.param_space.items():
                # Skip parameters that are constrained
                if parameters and param_name in parameters:
                    continue
                space[param_name] = param_value
            
            # Define objective function for hyperopt
            def objective_func(params):
                # Convert integer parameters
                for param in ['macd_fast', 'macd_slow', 'macd_signal', 'rsi_period', 
                             'stochastic_k_period', 'stochastic_d_period', 'sell_rolling_std', 
                             'buy_rolling_std']:
                    if param in params:
                        params[param] = int(params[param])
                
                # Handle fractal_lags based on window size
                if 'fractal_window' in params:
                    window = int(params['fractal_window'])
                    if window <= 50:
                        params['fractal_lags'] = [5, 10, 20]
                    elif window <= 100:
                        params['fractal_lags'] = [10, 20, 40]
                    else:
                        params['fractal_lags'] = [15, 30, 60]
                
                # Extract weights from weights_index
                if 'weights_index' in params:
                    params['weights'] = params.pop('weights_index')
                
                # Merge with base parameters
                test_params = copy.deepcopy(base_params)
                test_params.update(params)
                
                # Run backtest for each asset and aggregate results
                results = []
                for asset_id, data in market_data.items():
                    if data.empty:
                        continue
                    
                    try:
                        backtest_result = self._run_backtest(data, test_params)
                        results.append(backtest_result)
                    except Exception as e:
                        logger.error(f"Error in backtest for asset {asset_id}: {str(e)}")
                        # Continue with other assets
                
                if not results:
                    # Return poor performance if no valid results
                    return {
                        'loss': -0.0,  # Hyperopt minimizes, so negative for maximization
                        'status': STATUS_OK,
                        'metrics': {
                            'sharpe_ratio': 0.0,
                            'total_return': 0.0,
                            'max_drawdown': 0.0,
                            'win_rate': 0.0
                        }
                    }
                
                # Aggregate metrics across all assets
                sharpe_ratios = [r['metrics']['sharpe_ratio'] for r in results]
                total_returns = [r['metrics']['total_return'] for r in results]
                max_drawdowns = [r['metrics']['max_drawdown'] for r in results]
                win_rates = [r['metrics']['win_rate'] for r in results]
                
                # Calculate average metrics
                avg_sharpe = sum(sharpe_ratios) / len(sharpe_ratios)
                avg_return = sum(total_returns) / len(total_returns)
                avg_drawdown = sum(max_drawdowns) / len(max_drawdowns)
                avg_win_rate = sum(win_rates) / len(win_rates)
                
                # Determine loss based on objective
                if objective == 'sharpe_ratio':
                    loss = -avg_sharpe  # Negative because hyperopt minimizes
                elif objective == 'total_return':
                    loss = -avg_return
                elif objective == 'max_drawdown':
                    loss = avg_drawdown  # No negative needed, we want to minimize drawdown
                elif objective == 'win_rate':
                    loss = -avg_win_rate
                else:
                    # Default to Sharpe ratio
                    loss = -avg_sharpe
                
                # Return loss and metrics
                return {
                    'loss': loss,
                    'status': STATUS_OK,
                    'metrics': {
                        'sharpe_ratio': avg_sharpe,
                        'total_return': avg_return,
                        'max_drawdown': avg_drawdown,
                        'win_rate': avg_win_rate
                    }
                }
            
            # Set up trials object for tracking
            trials = Trials()
            
            # Run hyperopt optimization
            logger.info(f"Starting optimization for strategy {strategy_id} with {len(assets)} assets")
            
            # If task_id provided, set up progress callback
            if task_id:
                progress_callback = lambda p: self._update_task_progress(task_id, p)
            else:
                progress_callback = None
            
            # Run optimization with max_evals determined by complexity
            max_evals = min(100, max(20, 10 * len(assets)))
            
            # Capture best parameters as hyperopt minimizes the objective function
            best = fmin(
                fn=objective_func,
                space=space,
                algo=tpe.suggest,
                max_evals=max_evals,
                trials=trials,
                show_progressbar=False
            )
            
            # Get best parameters from hyperopt and combine with base parameters
            best_params = copy.deepcopy(base_params)
            
            # Process integer parameters
            for param in ['macd_fast', 'macd_slow', 'macd_signal', 'rsi_period', 
                         'stochastic_k_period', 'stochastic_d_period', 'sell_rolling_std', 
                         'buy_rolling_std']:
                if param in best:
                    best_params[param] = int(best[param])
            
            # Handle other parameters
            for param, value in best.items():
                if param in ['macd_fast', 'macd_slow', 'macd_signal', 'rsi_period', 
                            'stochastic_k_period', 'stochastic_d_period', 'sell_rolling_std', 
                            'buy_rolling_std']:
                    continue  # Already handled above
                elif param == 'weights_index':
                    # Get weights from choices
                    best_params['weights'] = self.param_space['weights_index'].pos_args[1][value]
                elif param == 'fractal_window':
                    # Get window from choices
                    best_params['fractal_window'] = self.param_space['fractal_window'].pos_args[1][value]
                    # Update fractal_lags based on window
                    window = best_params['fractal_window']
                    if window <= 50:
                        best_params['fractal_lags'] = [5, 10, 20]
                    elif window <= 100:
                        best_params['fractal_lags'] = [10, 20, 40]
                    else:
                        best_params['fractal_lags'] = [15, 30, 60]
                else:
                    best_params[param] = value
            
            # Get the best trial's metrics
            best_trial_idx = np.argmin([t['result']['loss'] for t in trials.trials])
            best_metrics = trials.trials[best_trial_idx]['result']['metrics']
            
            # Store optimization results in database
            optimization_data = {
                'strategy_id': strategy_id,
                'parameters': best_params,
                'metrics': best_metrics,
                'timestamp': datetime.utcnow()
            }
            
            result = StrategyRepository.create_strategy_optimization(db, optimization_data)
            
            # Also update strategy parameters
            StrategyRepository.update_strategy(db, strategy_id, {'parameters': best_params})
            
            # Update task status if provided
            if task_id:
                self._update_task_status(task_id, {
                    'strategy_id': strategy_id,
                    'status': 'completed',
                    'progress': 1.0,
                    'started_at': None,  # Keep existing value
                    'finished_at': datetime.utcnow(),
                    'error': None
                })
            
            logger.info(f"Optimization completed for strategy {strategy_id}")
            
            return {
                'strategy_id': strategy_id,
                'parameters': best_params,
                'metrics': best_metrics
            }
            
        except Exception as e:
            logger.error(f"Error in optimization for strategy {strategy_id}: {str(e)}")
            
            # Update task status if provided
            if task_id:
                self._update_task_status(task_id, {
                    'strategy_id': strategy_id,
                    'status': 'failed',
                    'progress': 0.0,
                    'started_at': None,  # Keep existing value
                    'finished_at': datetime.utcnow(),
                    'error': str(e)
                })
            
            raise
    
    def _run_backtest(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run backtest with given parameters
        
        Args:
            data: Market data DataFrame with OHLCV columns
            params: Strategy parameters
            
        Returns:
            Backtest results
        """
        try:
            # Import generate_signals function from indicators module
            # Note: In a real implementation, this would be a proper import
            # For our implementation, we'll create a simplified version
            
            # Generate signals based on parameters
            signals = self._generate_signals(data, params)
            
            # Run backtest
            initial_capital = 10000.0
            position = 0
            cash = initial_capital
            portfolio_value = []
            trades = []
            
            for i in range(1, len(signals)):
                signal = signals.iloc[i]['signal']
                price = data.iloc[i]['close']
                
                # Execute trades based on signals
                if signal == 1 and position == 0:  # Buy signal
                    # Calculate position size (equal to available cash)
                    shares = cash / price
                    position = shares
                    cash = 0
                    trades.append({'type': 'buy', 'price': price, 'shares': shares})
                elif signal == -1 and position > 0:  # Sell signal
                    # Calculate proceeds
                    proceeds = position * price
                    cash = proceeds
                    trades.append({'type': 'sell', 'price': price, 'shares': position})
                    position = 0
                
                # Calculate current portfolio value
                current_value = cash + (position * price)
                portfolio_value.append(current_value)
            
            # Calculate performance metrics
            if not portfolio_value:
                return {
                    'metrics': {
                        'sharpe_ratio': 0.0,
                        'total_return': 0.0,
                        'max_drawdown': 0.0,
                        'win_rate': 0.0
                    }
                }
            
            # Calculate returns
            returns = np.diff(portfolio_value) / portfolio_value[:-1]
            
            # Calculate metrics
            total_return = (portfolio_value[-1] / initial_capital - 1) * 100
            
            # Calculate Sharpe ratio (annualized)
            sharpe_ratio = 0.0
            if len(returns) > 0 and np.std(returns) > 0:
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
            
            # Calculate maximum drawdown
            cumulative = np.array(portfolio_value) / initial_capital
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (running_max - cumulative) / running_max
            max_drawdown = np.max(drawdown) * 100
            
            # Calculate win rate
            if not trades:
                win_rate = 0.0
            else:
                # Pair buy and sell trades to calculate win/loss
                wins = 0
                losses = 0
                buy_price = None
                
                for trade in trades:
                    if trade['type'] == 'buy':
                        buy_price = trade['price']
                    elif trade['type'] == 'sell' and buy_price is not None:
                        if trade['price'] > buy_price:
                            wins += 1
                        else:
                            losses += 1
                        buy_price = None
                
                total_closed_trades = wins + losses
                win_rate = (wins / total_closed_trades * 100) if total_closed_trades > 0 else 0.0
            
            return {
                'metrics': {
                    'sharpe_ratio': float(sharpe_ratio),
                    'total_return': float(total_return),
                    'max_drawdown': float(max_drawdown),
                    'win_rate': float(win_rate)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in backtest: {str(e)}")
            raise
    
    def _generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Generate trading signals based on indicators
        
        Args:
            data: Market data DataFrame with OHLCV columns
            params: Strategy parameters
            
        Returns:
            DataFrame with signals
        """
        # This is a simplified version of the generate_signals function
        # In a real implementation, this would use the actual function from indicators.py
        
        # Initialize signals DataFrame
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        
        # Calculate MACD
        fast = params.get('macd_fast', 12)
        slow = params.get('macd_slow', 26)
        signal_period = params.get('macd_signal', 9)
        
        ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['close'].ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal_period, adjust=False).mean()
        macd_hist = macd - macd_signal
        
        # Calculate RSI
        rsi_period = params.get('rsi_period', 14)
        delta = data['close'].diff()
        gain = delta.clip(lower=0).rolling(window=rsi_period).mean()
        loss = -delta.clip(upper=0).rolling(window=rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Calculate simple thresholds for signals
        signals.loc[macd_hist > 0, 'signal'] = 1  # Buy when MACD histogram is positive
        signals.loc[(macd_hist < 0) & (rsi < 30), 'signal'] = -1  # Sell when MACD histogram is negative and RSI is oversold
        
        return signals
    
    def get_optimization_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of an optimization task
        
        Args:
            task_id: Task ID to check
            
        Returns:
            Task status or None if not found
        """
        with optimization_tasks_lock:
            return optimization_tasks.get(task_id)
    
    def _update_task_status(self, task_id: str, status: Dict[str, Any]) -> None:
        """
        Update the status of an optimization task
        
        Args:
            task_id: Task ID to update
            status: New status information
        """
        with optimization_tasks_lock:
            existing = optimization_tasks.get(task_id, {})
            # Preserve existing values for fields that are None in the update
            for key, value in status.items():
                if value is not None or key not in existing:
                    existing[key] = value
            optimization_tasks[task_id] = existing
    
    def _update_task_progress(self, task_id: str, progress: float) -> None:
        """
        Update the progress of an optimization task
        
        Args:
            task_id: Task ID to update
            progress: Progress value (0.0 to 1.0)
        """
        with optimization_tasks_lock:
            if task_id in optimization_tasks:
                optimization_tasks[task_id]['progress'] = progress

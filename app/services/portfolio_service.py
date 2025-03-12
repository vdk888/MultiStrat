import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from sqlalchemy.orm import Session

from app.database.repository.portfolios import PortfolioRepository
from app.database.repository.assets import AssetRepository
from app.database.models import Portfolio, PortfolioAsset, PerformanceMetric, Trade
from app.services.data_service import DataService
from app.utils.metrics import calculate_sharpe_ratio, calculate_max_drawdown, calculate_volatility
from app.core.config import get_settings

# Set up logger
logger = logging.getLogger(__name__)

# Dictionary to store rebalance task statuses
rebalance_tasks = {}

class PortfolioService:
    """
    Service for portfolio management operations
    """
    
    def __init__(self):
        """Initialize the portfolio service"""
        self.settings = get_settings()
        self.data_service = DataService()
        self.rebalance_threshold = 0.05  # 5% threshold for rebalancing
    
    def calculate_performance(self, db: Session, portfolio_id: int) -> PerformanceMetric:
        """
        Calculate performance metrics for a portfolio
        
        Args:
            db: Database session
            portfolio_id: Portfolio ID
            
        Returns:
            PerformanceMetric record
        """
        try:
            # Get portfolio
            portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
            if not portfolio:
                raise ValueError(f"Portfolio with ID {portfolio_id} not found")
            
            # Get portfolio assets
            portfolio_assets = PortfolioRepository.get_portfolio_assets(db, portfolio_id=portfolio_id)
            if not portfolio_assets:
                logger.warning(f"No assets found for portfolio {portfolio_id}")
                return self._create_empty_performance_metric(db, portfolio_id)
            
            # Get historical data for portfolio assets
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)  # Last 30 days for metrics
            
            # Fetch asset prices and calculate portfolio values
            portfolio_values = []
            asset_symbols = []
            asset_quantities = []
            
            for asset in portfolio_assets:
                db_asset = AssetRepository.get_asset(db, asset_id=asset.asset_id)
                if not db_asset:
                    continue
                
                symbol = db_asset.yfinance_symbol or db_asset.symbol
                asset_symbols.append(symbol)
                asset_quantities.append(asset.quantity)
            
            if not asset_symbols:
                logger.warning(f"No valid symbols found for portfolio {portfolio_id}")
                return self._create_empty_performance_metric(db, portfolio_id)
            
            # Fetch historical data for all symbols
            historical_data = {}
            for symbol in asset_symbols:
                try:
                    data = self.data_service.get_historical_data(symbol, days=30)
                    if data:
                        # Convert to DataFrame for easier processing
                        df = pd.DataFrame(data)
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df.set_index('timestamp', inplace=True)
                        historical_data[symbol] = df
                except Exception as e:
                    logger.error(f"Error fetching data for {symbol}: {str(e)}")
            
            if not historical_data:
                logger.warning(f"No historical data available for portfolio {portfolio_id}")
                return self._create_empty_performance_metric(db, portfolio_id)
            
            # Create daily portfolio values
            # Resample all data to daily frequency for consistent dates
            daily_values = []
            dates = []
            
            # Get unique sorted dates from all historical data
            all_dates = set()
            for symbol, data in historical_data.items():
                all_dates.update(data.index.date)
            
            all_dates = sorted(all_dates)
            
            # Calculate portfolio value for each date
            for date in all_dates:
                total_value = 0
                
                for i, (symbol, quantity) in enumerate(zip(asset_symbols, asset_quantities)):
                    if symbol in historical_data:
                        # Find the closest data point for this date
                        date_data = historical_data[symbol][historical_data[symbol].index.date == date]
                        if not date_data.empty:
                            price = date_data['close'].iloc[-1]
                            total_value += price * quantity
                
                if total_value > 0:
                    daily_values.append(total_value)
                    dates.append(date)
            
            # Convert to numpy arrays for calculations
            daily_values = np.array(daily_values)
            
            if len(daily_values) < 2:
                logger.warning(f"Insufficient data points for portfolio {portfolio_id}")
                return self._create_empty_performance_metric(db, portfolio_id)
            
            # Calculate returns
            daily_returns = np.diff(daily_values) / daily_values[:-1]
            
            # Calculate metrics
            current_value = daily_values[-1]
            initial_value = daily_values[0]
            total_return = (current_value / initial_value - 1) * 100
            daily_return = daily_returns[-1] * 100 if len(daily_returns) > 0 else 0
            
            # Calculate advanced metrics
            sharpe_ratio = calculate_sharpe_ratio(daily_returns)
            max_drawdown = calculate_max_drawdown(daily_values)
            volatility = calculate_volatility(daily_returns)
            
            # Calculate win rate from trades
            trades = PortfolioRepository.get_trades(
                db, 
                portfolio_id=portfolio_id, 
                start_date=start_date
            )
            
            win_rate = self._calculate_win_rate(trades)
            
            # Update portfolio current value
            PortfolioRepository.update_portfolio(
                db, 
                portfolio_id, 
                {"current_value": float(current_value)}
            )
            
            # Create performance metric record
            metric_data = {
                "portfolio_id": portfolio_id,
                "timestamp": datetime.utcnow(),
                "total_return": float(total_return),
                "daily_return": float(daily_return),
                "sharpe_ratio": float(sharpe_ratio),
                "max_drawdown": float(max_drawdown),
                "volatility": float(volatility),
                "win_rate": float(win_rate),
                "additional_metrics": {
                    "current_value": float(current_value),
                    "initial_value": float(initial_value),
                    "num_trades": len(trades)
                }
            }
            
            return PortfolioRepository.add_performance_metric(db, metric_data)
            
        except Exception as e:
            logger.error(f"Error calculating performance for portfolio {portfolio_id}: {str(e)}")
            # Create empty metric with error details
            return self._create_empty_performance_metric(db, portfolio_id, error=str(e))
    
    def _create_empty_performance_metric(self, 
                                        db: Session, 
                                        portfolio_id: int, 
                                        error: str = None) -> PerformanceMetric:
        """Create empty performance metric when calculation fails"""
        metric_data = {
            "portfolio_id": portfolio_id,
            "timestamp": datetime.utcnow(),
            "total_return": 0.0,
            "daily_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "volatility": 0.0,
            "win_rate": 0.0,
            "additional_metrics": {
                "error": error or "Insufficient data for calculation"
            }
        }
        
        return PortfolioRepository.add_performance_metric(db, metric_data)
    
    def _calculate_win_rate(self, trades: List[Trade]) -> float:
        """Calculate win rate from trades"""
        if not trades:
            return 0.0
        
        # Count successful trades (sell price > buy price)
        buy_price = None
        win_count = 0
        trade_count = 0
        
        for trade in sorted(trades, key=lambda t: t.timestamp):
            if trade.side.lower() == "buy":
                buy_price = trade.price
            elif trade.side.lower() == "sell" and buy_price is not None:
                if trade.price > buy_price:
                    win_count += 1
                trade_count += 1
                buy_price = None
        
        return (win_count / trade_count * 100) if trade_count > 0 else 0.0
    
    def check_rebalance_needed(self, db: Session, portfolio_id: int) -> Tuple[bool, float]:
        """
        Check if a portfolio needs rebalancing
        
        Args:
            db: Database session
            portfolio_id: Portfolio ID
            
        Returns:
            Tuple of (needs_rebalance, max_deviation)
        """
        try:
            # Get portfolio
            portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
            if not portfolio:
                raise ValueError(f"Portfolio with ID {portfolio_id} not found")
            
            # Get portfolio assets
            portfolio_assets = PortfolioRepository.get_portfolio_assets(db, portfolio_id=portfolio_id)
            if not portfolio_assets:
                logger.warning(f"No assets found for portfolio {portfolio_id}")
                return False, 0.0
            
            # Get current prices for assets
            asset_symbols = []
            for asset in portfolio_assets:
                db_asset = AssetRepository.get_asset(db, asset_id=asset.asset_id)
                if db_asset:
                    symbol = db_asset.yfinance_symbol or db_asset.symbol
                    asset_symbols.append((asset.asset_id, symbol))
            
            if not asset_symbols:
                logger.warning(f"No valid symbols found for portfolio {portfolio_id}")
                return False, 0.0
            
            # Fetch current prices
            symbols = [s[1] for s in asset_symbols]
            current_prices = self.data_service.get_current_prices(symbols)
            
            # Calculate current allocations
            total_value = 0
            asset_values = {}
            
            for asset in portfolio_assets:
                for asset_id, symbol in asset_symbols:
                    if asset.asset_id == asset_id and symbol in current_prices:
                        price = current_prices[symbol]
                        value = asset.quantity * price
                        asset_values[asset.asset_id] = value
                        total_value += value
            
            if total_value == 0:
                logger.warning(f"Portfolio {portfolio_id} has zero value")
                return False, 0.0
            
            # Calculate allocation deviations
            max_deviation = 0
            
            for asset in portfolio_assets:
                if asset.asset_id in asset_values:
                    current_allocation = asset_values[asset.asset_id] / total_value
                    deviation = abs(current_allocation - asset.target_allocation)
                    
                    # Update current allocation in database
                    PortfolioRepository.update_portfolio_asset(
                        db, 
                        portfolio_id, 
                        asset.asset_id, 
                        {"current_allocation": float(current_allocation)}
                    )
                    
                    max_deviation = max(max_deviation, deviation)
            
            # Check if rebalance is needed
            needs_rebalance = max_deviation > self.rebalance_threshold
            
            return needs_rebalance, max_deviation * 100  # Convert to percentage
            
        except Exception as e:
            logger.error(f"Error checking rebalance for portfolio {portfolio_id}: {str(e)}")
            return False, 0.0
    
    def rebalance_portfolio(self, 
                           db: Session, 
                           portfolio_id: int, 
                           max_trades: Optional[int] = None, 
                           trade_limit_pct: Optional[float] = None,
                           task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Rebalance a portfolio to target allocations
        
        Args:
            db: Database session
            portfolio_id: Portfolio ID
            max_trades: Maximum number of trades to generate
            trade_limit_pct: Maximum percentage of portfolio to trade
            task_id: Optional task ID for tracking status
            
        Returns:
            Rebalance results
        """
        # Update task status if provided
        if task_id:
            rebalance_tasks[task_id] = {
                "portfolio_id": portfolio_id,
                "status": "running",
                "progress": 0.0,
                "started_at": datetime.utcnow()
            }
        
        try:
            # Get portfolio
            portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
            if not portfolio:
                raise ValueError(f"Portfolio with ID {portfolio_id} not found")
            
            # Get portfolio assets
            portfolio_assets = PortfolioRepository.get_portfolio_assets(db, portfolio_id=portfolio_id)
            if not portfolio_assets:
                raise ValueError(f"No assets found for portfolio {portfolio_id}")
            
            # Update progress
            if task_id:
                rebalance_tasks[task_id]["progress"] = 0.1
            
            # Get current prices for assets
            asset_map = {}
            asset_symbols = []
            
            for asset in portfolio_assets:
                db_asset = AssetRepository.get_asset(db, asset_id=asset.asset_id)
                if db_asset:
                    symbol = db_asset.yfinance_symbol or db_asset.symbol
                    asset_map[asset.asset_id] = {
                        "symbol": symbol,
                        "asset_obj": db_asset,
                        "portfolio_asset": asset
                    }
                    asset_symbols.append(symbol)
            
            if not asset_symbols:
                raise ValueError(f"No valid symbols found for portfolio {portfolio_id}")
            
            # Update progress
            if task_id:
                rebalance_tasks[task_id]["progress"] = 0.2
            
            # Fetch current prices
            current_prices = self.data_service.get_current_prices(asset_symbols)
            
            # Update progress
            if task_id:
                rebalance_tasks[task_id]["progress"] = 0.3
            
            # Calculate current allocations and target values
            total_value = 0
            asset_values = {}
            
            for asset_id, data in asset_map.items():
                symbol = data["symbol"]
                portfolio_asset = data["portfolio_asset"]
                
                if symbol in current_prices:
                    price = current_prices[symbol]
                    value = portfolio_asset.quantity * price
                    asset_values[asset_id] = value
                    total_value += value
                    
                    # Update current price in database
                    PortfolioRepository.update_portfolio_asset(
                        db, 
                        portfolio_id, 
                        asset_id, 
                        {"current_price": float(price)}
                    )
            
            if total_value == 0:
                raise ValueError(f"Portfolio {portfolio_id} has zero value")
            
            # Update progress
            if task_id:
                rebalance_tasks[task_id]["progress"] = 0.4
            
            # Calculate target values and required trades
            trades_needed = []
            
            for asset_id, data in asset_map.items():
                portfolio_asset = data["portfolio_asset"]
                symbol = data["symbol"]
                
                if asset_id in asset_values and symbol in current_prices:
                    current_value = asset_values[asset_id]
                    current_allocation = current_value / total_value
                    target_allocation = portfolio_asset.target_allocation
                    
                    # Update current allocation in database
                    PortfolioRepository.update_portfolio_asset(
                        db, 
                        portfolio_id, 
                        asset_id, 
                        {"current_allocation": float(current_allocation)}
                    )
                    
                    # Calculate target value and difference
                    target_value = total_value * target_allocation
                    value_diff = target_value - current_value
                    
                    if abs(value_diff) > 0:
                        # Calculate shares to trade
                        price = current_prices[symbol]
                        shares = value_diff / price
                        
                        # Add to trades list
                        trades_needed.append({
                            "asset_id": asset_id,
                            "symbol": symbol,
                            "price": price,
                            "shares": shares,
                            "value": value_diff,
                            "side": "buy" if shares > 0 else "sell"
                        })
            
            # Sort trades by absolute value
            trades_needed.sort(key=lambda t: abs(t["value"]), reverse=True)
            
            # Update progress
            if task_id:
                rebalance_tasks[task_id]["progress"] = 0.5
            
            # Apply trade limits if specified
            if max_trades and max_trades > 0:
                trades_needed = trades_needed[:max_trades]
            
            if trade_limit_pct and trade_limit_pct > 0:
                max_trade_value = total_value * (trade_limit_pct / 100)
                
                # Limit trades to specified percentage
                limited_trades = []
                cumulative_value = 0
                
                for trade in trades_needed:
                    if cumulative_value + abs(trade["value"]) <= max_trade_value:
                        limited_trades.append(trade)
                        cumulative_value += abs(trade["value"])
                    else:
                        # Add partial trade if possible
                        remaining = max_trade_value - cumulative_value
                        if remaining > 0:
                            ratio = remaining / abs(trade["value"])
                            partial_trade = trade.copy()
                            partial_trade["shares"] *= ratio
                            partial_trade["value"] *= ratio
                            limited_trades.append(partial_trade)
                        break
                
                trades_needed = limited_trades
            
            # Update progress
            if task_id:
                rebalance_tasks[task_id]["progress"] = 0.7
            
            # Create trade records
            executed_trades = []
            
            for trade in trades_needed:
                if abs(trade["shares"]) < 0.0001:
                    continue  # Skip very small trades
                
                # Create trade record
                trade_data = {
                    "portfolio_id": portfolio_id,
                    "asset_id": trade["asset_id"],
                    "timestamp": datetime.utcnow(),
                    "order_type": "market",
                    "side": trade["side"],
                    "quantity": abs(float(trade["shares"])),
                    "price": float(trade["price"]),
                    "status": "pending",
                    "notes": "Auto-rebalance"
                }
                
                db_trade = PortfolioRepository.add_trade(db, trade_data)
                executed_trades.append(db_trade)
                
                # Update portfolio asset quantity
                asset = asset_map[trade["asset_id"]]["portfolio_asset"]
                new_quantity = asset.quantity + trade["shares"]
                
                PortfolioRepository.update_portfolio_asset(
                    db, 
                    portfolio_id, 
                    trade["asset_id"], 
                    {
                        "quantity": float(max(0, new_quantity)),  # Ensure non-negative
                        "last_rebalanced": datetime.utcnow()
                    }
                )
            
            # Update progress
            if task_id:
                rebalance_tasks[task_id]["progress"] = 0.9
            
            # Update trade statuses to completed (in a real system, this would happen after actual execution)
            for trade in executed_trades:
                PortfolioRepository.update_trade(
                    db, 
                    trade.id, 
                    {"status": "filled"}
                )
            
            # Update task status if provided
            if task_id:
                rebalance_tasks[task_id] = {
                    "portfolio_id": portfolio_id,
                    "status": "completed",
                    "progress": 1.0,
                    "started_at": rebalance_tasks[task_id]["started_at"],
                    "finished_at": datetime.utcnow(),
                    "trades_count": len(executed_trades)
                }
            
            # Calculate performance after rebalance
            self.calculate_performance(db, portfolio_id)
            
            return {
                "portfolio_id": portfolio_id,
                "trades_executed": len(executed_trades),
                "total_value": float(total_value),
                "rebalance_complete": True
            }
            
        except Exception as e:
            logger.error(f"Error rebalancing portfolio {portfolio_id}: {str(e)}")
            
            # Update task status if provided
            if task_id and task_id in rebalance_tasks:
                rebalance_tasks[task_id]["status"] = "failed"
                rebalance_tasks[task_id]["error"] = str(e)
                rebalance_tasks[task_id]["finished_at"] = datetime.utcnow()
            
            raise
    
    def get_rebalance_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a rebalance task
        
        Args:
            task_id: Task ID to check
            
        Returns:
            Task status or None if not found
        """
        return rebalance_tasks.get(task_id)

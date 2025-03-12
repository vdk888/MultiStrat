import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from sqlalchemy.orm import Session
import threading

from app.database.repository.portfolios import PortfolioRepository
from app.database.repository.strategies import StrategyRepository
from app.services.data_service import DataService
from app.utils.metrics import calculate_sharpe_ratio
from app.core.config import get_settings

# Set up logger
logger = logging.getLogger(__name__)

# Dictionary to store allocation optimization task statuses
allocation_tasks = {}
allocation_tasks_lock = threading.Lock()

class AllocationService:
    """
    Service for portfolio allocation optimization
    """
    
    def __init__(self):
        """Initialize the allocation service"""
        self.settings = get_settings()
        self.data_service = DataService()
        self.default_lookback_days = 180  # Longer lookback for allocation optimization
    
    def optimize_allocation(self, db: Session, portfolio_id: int, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Optimize strategy allocations for a portfolio using various methods
        
        Args:
            db: Database session
            portfolio_id: Portfolio ID to optimize
            task_id: Optional task ID for tracking status
            
        Returns:
            Optimization results
        """
        # Set task status to running
        if task_id:
            self._update_task_status(task_id, {
                'portfolio_id': portfolio_id,
                'status': 'running',
                'progress': 0.0,
                'started_at': datetime.utcnow(),
                'finished_at': None,
                'error': None
            })
        
        try:
            # Get portfolio
            portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
            if not portfolio:
                raise ValueError(f"Portfolio with ID {portfolio_id} not found")
            
            # Get portfolio strategies
            portfolio_strategies = PortfolioRepository.get_portfolio_strategies(db, portfolio_id=portfolio_id)
            if not portfolio_strategies:
                raise ValueError(f"No strategies found for portfolio {portfolio_id}")
            
            # Update progress
            if task_id:
                self._update_task_progress(task_id, 0.1)
            
            # Collect strategy performance data
            strategy_data = []
            
            for ps in portfolio_strategies:
                # Get strategy
                strategy = StrategyRepository.get_strategy(db, strategy_id=ps.strategy_id)
                if not strategy:
                    continue
                
                # Get strategy optimization results (for performance metrics)
                latest_optimization = StrategyRepository.get_latest_strategy_optimization(db, strategy_id=ps.strategy_id)
                
                strategy_data.append({
                    'portfolio_strategy_id': ps.id,
                    'strategy_id': ps.strategy_id,
                    'name': strategy.name,
                    'current_allocation': ps.allocation,
                    'metrics': latest_optimization.metrics if latest_optimization else {},
                    'parameters': strategy.parameters,
                    'is_active': ps.is_active
                })
            
            # Update progress
            if task_id:
                self._update_task_progress(task_id, 0.2)
            
            # Filter active strategies with metrics
            active_strategies = [s for s in strategy_data if s['is_active'] and s['metrics']]
            
            if not active_strategies:
                raise ValueError(f"No active strategies with performance metrics for portfolio {portfolio_id}")
            
            # Extract metrics for optimization
            returns = []
            sharpe_ratios = []
            risks = []
            
            for strategy in active_strategies:
                metrics = strategy['metrics']
                
                # Get key metrics (with defaults for missing values)
                returns.append(metrics.get('total_return', 0.0))
                sharpe_ratios.append(metrics.get('sharpe_ratio', 0.0))
                
                # Use max_drawdown as risk measure (invert since we want to minimize)
                risk = metrics.get('max_drawdown', 0.0)
                # Ensure non-zero risk for calculations
                risks.append(max(risk, 0.01))
            
            # Convert to numpy arrays
            returns = np.array(returns)
            sharpe_ratios = np.array(sharpe_ratios)
            risks = np.array(risks)
            
            # Update progress
            if task_id:
                self._update_task_progress(task_id, 0.3)
            
            # Calculate multiple allocation approaches
            allocations = {}
            
            # 1. Equal weight allocation
            equal_weight = np.ones(len(active_strategies)) / len(active_strategies)
            allocations['equal_weight'] = equal_weight
            
            # 2. Return-weighted allocation
            # Handle negative returns by shifting to ensure all values are positive
            returns_for_weight = returns.copy()
            if np.min(returns_for_weight) < 0:
                returns_for_weight = returns_for_weight - np.min(returns_for_weight) + 0.1
            
            return_weight = returns_for_weight / np.sum(returns_for_weight)
            allocations['return_weighted'] = return_weight
            
            # 3. Sharpe-weighted allocation
            # Handle negative Sharpe ratios
            sharpe_for_weight = sharpe_ratios.copy()
            if np.min(sharpe_for_weight) < 0:
                sharpe_for_weight = sharpe_for_weight - np.min(sharpe_for_weight) + 0.1
            
            sharpe_weight = sharpe_for_weight / np.sum(sharpe_for_weight)
            allocations['sharpe_weighted'] = sharpe_weight
            
            # 4. Risk parity allocation
            # Inverse risk weighting
            inv_risk = 1.0 / risks
            risk_parity = inv_risk / np.sum(inv_risk)
            allocations['risk_parity'] = risk_parity
            
            # 5. Risk-adjusted return allocation
            risk_adj_return = returns / risks
            # Handle negative values
            if np.min(risk_adj_return) < 0:
                risk_adj_return = risk_adj_return - np.min(risk_adj_return) + 0.1
            
            risk_adj_weight = risk_adj_return / np.sum(risk_adj_return)
            allocations['risk_adjusted'] = risk_adj_weight
            
            # Update progress
            if task_id:
                self._update_task_progress(task_id, 0.5)
            
            # Choose allocation method based on portfolio risk tolerance
            # Higher risk tolerance -> more return-weighted
            # Lower risk tolerance -> more risk parity
            risk_tolerance = portfolio.risk_tolerance
            
            # Blend allocation methods based on risk tolerance
            if risk_tolerance <= 0.25:
                # Low risk: 75% risk parity, 25% sharpe-weighted
                final_allocation = 0.75 * allocations['risk_parity'] + 0.25 * allocations['sharpe_weighted']
            elif risk_tolerance <= 0.5:
                # Medium-low risk: 50% risk parity, 50% sharpe-weighted
                final_allocation = 0.5 * allocations['risk_parity'] + 0.5 * allocations['sharpe_weighted']
            elif risk_tolerance <= 0.75:
                # Medium-high risk: 50% sharpe-weighted, 50% risk-adjusted
                final_allocation = 0.5 * allocations['sharpe_weighted'] + 0.5 * allocations['risk_adjusted']
            else:
                # High risk: 25% sharpe-weighted, 75% risk-adjusted
                final_allocation = 0.25 * allocations['sharpe_weighted'] + 0.75 * allocations['risk_adjusted']
            
            # Normalize to ensure allocations sum to 1
            final_allocation = final_allocation / np.sum(final_allocation)
            
            # Update progress
            if task_id:
                self._update_task_progress(task_id, 0.7)
            
            # Update strategy allocations in database
            results = []
            
            for i, strategy in enumerate(active_strategies):
                # Update portfolio strategy allocation
                updated = PortfolioRepository.update_strategy_allocation(
                    db, 
                    portfolio_id, 
                    strategy['strategy_id'], 
                    allocation=float(final_allocation[i])
                )
                
                if updated:
                    results.append({
                        'strategy_id': strategy['strategy_id'],
                        'name': strategy['name'],
                        'previous_allocation': strategy['current_allocation'],
                        'new_allocation': float(final_allocation[i]),
                        'change': float(final_allocation[i] - strategy['current_allocation'])
                    })
            
            # Update progress
            if task_id:
                self._update_task_progress(task_id, 0.9)
            
            # Calculate allocation metrics for different methods
            allocation_metrics = {}
            for method, alloc in allocations.items():
                # Calculate expected return and risk
                expected_return = np.sum(alloc * returns)
                # Simple portfolio risk calculation
                portfolio_risk = np.sqrt(np.sum((alloc * risks) ** 2))
                # Simple Sharpe proxy
                sharpe = expected_return / portfolio_risk if portfolio_risk > 0 else 0
                
                allocation_metrics[method] = {
                    'expected_return': float(expected_return),
                    'risk': float(portfolio_risk),
                    'sharpe': float(sharpe)
                }
            
            # Also calculate for final allocation
            expected_return = np.sum(final_allocation * returns)
            portfolio_risk = np.sqrt(np.sum((final_allocation * risks) ** 2))
            sharpe = expected_return / portfolio_risk if portfolio_risk > 0 else 0
            
            allocation_metrics['final'] = {
                'expected_return': float(expected_return),
                'risk': float(portfolio_risk),
                'sharpe': float(sharpe),
                'method': 'blended'
            }
            
            # Create result object
            result = {
                'portfolio_id': portfolio_id,
                'risk_tolerance': portfolio.risk_tolerance,
                'allocation_method': 'risk_adjusted_blend',
                'strategy_allocations': results,
                'allocation_metrics': allocation_metrics,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Update task status if provided
            if task_id:
                self._update_task_status(task_id, {
                    'portfolio_id': portfolio_id,
                    'status': 'completed',
                    'progress': 1.0,
                    'started_at': None,  # Keep existing value
                    'finished_at': datetime.utcnow(),
                    'error': None,
                    'result': result
                })
            
            logger.info(f"Allocation optimization completed for portfolio {portfolio_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in allocation optimization for portfolio {portfolio_id}: {str(e)}")
            
            # Update task status if provided
            if task_id:
                self._update_task_status(task_id, {
                    'portfolio_id': portfolio_id,
                    'status': 'failed',
                    'progress': 0.0,
                    'started_at': None,  # Keep existing value
                    'finished_at': datetime.utcnow(),
                    'error': str(e)
                })
            
            raise
    
    def get_allocation_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of an allocation optimization task
        
        Args:
            task_id: Task ID to check
            
        Returns:
            Task status or None if not found
        """
        with allocation_tasks_lock:
            return allocation_tasks.get(task_id)
    
    def _update_task_status(self, task_id: str, status: Dict[str, Any]) -> None:
        """
        Update the status of an allocation task
        
        Args:
            task_id: Task ID to update
            status: New status information
        """
        with allocation_tasks_lock:
            existing = allocation_tasks.get(task_id, {})
            # Preserve existing values for fields that are None in the update
            for key, value in status.items():
                if value is not None or key not in existing:
                    existing[key] = value
            allocation_tasks[task_id] = existing
    
    def _update_task_progress(self, task_id: str, progress: float) -> None:
        """
        Update the progress of an allocation task
        
        Args:
            task_id: Task ID to update
            progress: Progress value (0.0 to 1.0)
        """
        with allocation_tasks_lock:
            if task_id in allocation_tasks:
                allocation_tasks[task_id]['progress'] = progress

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from sqlalchemy.orm import Session
import logging
import os

from app.core.config import get_settings
from app.database.session import SessionLocal

# Set up logger
logger = logging.getLogger(__name__)

def setup_scheduler():
    """
    Set up and configure the APScheduler for background tasks
    """
    settings = get_settings()
    
    # Configure job stores and executors
    jobstores = {
        'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
    }
    executors = {
        'default': ThreadPoolExecutor(max_workers=5)
    }
    
    # Create scheduler
    scheduler = BackgroundScheduler(
        jobstores=jobstores,
        executors=executors,
        timezone=settings.SCHEDULER_TIMEZONE
    )
    
    if settings.SCHEDULER_ENABLED:
        # Add scheduled jobs
        add_scheduled_jobs(scheduler)
    
    return scheduler

def add_scheduled_jobs(scheduler):
    """
    Add all scheduled jobs to the scheduler
    """
    # Add daily optimization job
    scheduler.add_job(
        daily_optimization_job,
        'cron',
        hour=0,  # Midnight
        minute=0,
        id='daily_optimization_job',
        replace_existing=True
    )
    
    # Add data update job (every 4 hours)
    scheduler.add_job(
        data_update_job,
        'interval',
        hours=4,
        id='data_update_job',
        replace_existing=True
    )
    
    # Add performance calculation job (daily)
    scheduler.add_job(
        performance_calculation_job,
        'cron',
        hour=1,  # 1 AM
        minute=0,
        id='performance_calculation_job',
        replace_existing=True
    )
    
    # Add portfolio rebalancing check job (daily)
    scheduler.add_job(
        portfolio_rebalance_check_job,
        'cron',
        hour=2,  # 2 AM
        minute=0,
        id='portfolio_rebalance_check_job',
        replace_existing=True
    )
    
    logger.info("Scheduled jobs have been added to the scheduler")

def daily_optimization_job():
    """
    Job to run daily optimization for all active strategies
    """
    try:
        logger.info("Starting daily optimization job")
        db = SessionLocal()
        
        try:
            # Import here to avoid circular imports
            from app.services.optimization_service import OptimizationService
            from app.database.repository.strategies import StrategyRepository
            
            # Get all active strategies
            strategies = StrategyRepository.get_strategies(db)
            active_strategies = [s for s in strategies if s.is_active]
            
            if not active_strategies:
                logger.info("No active strategies found for optimization")
                return
            
            # Initialize optimization service
            optimization_service = OptimizationService()
            
            # Optimize each strategy
            for strategy in active_strategies:
                logger.info(f"Optimizing strategy: {strategy.name} (ID: {strategy.id})")
                try:
                    # Get assets for this strategy's asset class
                    assets = strategy.asset_class.assets
                    asset_ids = [a.id for a in assets if a.is_active]
                    
                    if not asset_ids:
                        logger.warning(f"No active assets found for strategy {strategy.name}")
                        continue
                    
                    # Run optimization
                    optimization_service.run_optimization(
                        db=db,
                        strategy_id=strategy.id,
                        asset_ids=asset_ids,
                        task_id=f"scheduled_optimize_{strategy.id}"
                    )
                    
                except Exception as e:
                    logger.error(f"Error optimizing strategy {strategy.name}: {str(e)}")
                    continue
            
            logger.info("Daily optimization job completed")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in daily optimization job: {str(e)}")

def data_update_job():
    """
    Job to update market data for all active assets
    """
    try:
        logger.info("Starting data update job")
        db = SessionLocal()
        
        try:
            # Import here to avoid circular imports
            from app.services.data_service import DataService
            from app.database.repository.assets import AssetRepository
            
            # Get all active assets
            assets = AssetRepository.get_assets(db)
            active_assets = [a for a in assets if a.is_active]
            
            if not active_assets:
                logger.info("No active assets found for data update")
                return
            
            # Initialize data service
            data_service = DataService()
            
            # Update data for each asset
            for asset in active_assets:
                logger.info(f"Updating data for asset: {asset.symbol}")
                try:
                    # Get appropriate symbol for API
                    symbol = asset.yfinance_symbol or asset.symbol
                    
                    # Fetch and store data
                    data_service.update_market_data(db, asset.id, symbol)
                    
                except Exception as e:
                    logger.error(f"Error updating data for asset {asset.symbol}: {str(e)}")
                    continue
            
            logger.info("Data update job completed")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in data update job: {str(e)}")

def performance_calculation_job():
    """
    Job to calculate performance metrics for all active portfolios
    """
    try:
        logger.info("Starting performance calculation job")
        db = SessionLocal()
        
        try:
            # Import here to avoid circular imports
            from app.services.portfolio_service import PortfolioService
            from app.database.repository.portfolios import PortfolioRepository
            
            # Get all active portfolios
            portfolios = PortfolioRepository.get_portfolios(db)
            active_portfolios = [p for p in portfolios if p.is_active]
            
            if not active_portfolios:
                logger.info("No active portfolios found for performance calculation")
                return
            
            # Initialize portfolio service
            portfolio_service = PortfolioService()
            
            # Calculate performance for each portfolio
            for portfolio in active_portfolios:
                logger.info(f"Calculating performance for portfolio: {portfolio.name}")
                try:
                    portfolio_service.calculate_performance(db, portfolio.id)
                except Exception as e:
                    logger.error(f"Error calculating performance for portfolio {portfolio.name}: {str(e)}")
                    continue
            
            logger.info("Performance calculation job completed")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in performance calculation job: {str(e)}")

def portfolio_rebalance_check_job():
    """
    Job to check if portfolios need rebalancing
    """
    try:
        logger.info("Starting portfolio rebalance check job")
        db = SessionLocal()
        
        try:
            # Import here to avoid circular imports
            from app.services.portfolio_service import PortfolioService
            from app.database.repository.portfolios import PortfolioRepository
            
            # Get all active portfolios
            portfolios = PortfolioRepository.get_portfolios(db)
            active_portfolios = [p for p in portfolios if p.is_active]
            
            if not active_portfolios:
                logger.info("No active portfolios found for rebalance check")
                return
            
            # Initialize portfolio service
            portfolio_service = PortfolioService()
            
            # Check rebalance for each portfolio
            for portfolio in active_portfolios:
                logger.info(f"Checking if portfolio needs rebalancing: {portfolio.name}")
                try:
                    needs_rebalance, threshold = portfolio_service.check_rebalance_needed(db, portfolio.id)
                    
                    if needs_rebalance:
                        logger.info(f"Portfolio {portfolio.name} needs rebalancing (threshold: {threshold:.2f}%)")
                        # Perform rebalance
                        portfolio_service.rebalance_portfolio(
                            db=db,
                            portfolio_id=portfolio.id,
                            task_id=f"scheduled_rebalance_{portfolio.id}"
                        )
                    else:
                        logger.info(f"Portfolio {portfolio.name} does not need rebalancing")
                    
                except Exception as e:
                    logger.error(f"Error checking rebalance for portfolio {portfolio.name}: {str(e)}")
                    continue
            
            logger.info("Portfolio rebalance check job completed")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in portfolio rebalance check job: {str(e)}")

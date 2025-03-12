from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import Portfolio, PortfolioStrategy, PortfolioAsset, PerformanceMetric, Trade

class PortfolioRepository:
    """
    Repository for portfolio-related database operations
    """
    
    @staticmethod
    def get_portfolio(db: Session, portfolio_id: int) -> Optional[Portfolio]:
        """Get portfolio by ID"""
        return db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    
    @staticmethod
    def get_portfolio_by_name(db: Session, name: str) -> Optional[Portfolio]:
        """Get portfolio by name"""
        return db.query(Portfolio).filter(Portfolio.name == name).first()
    
    @staticmethod
    def get_portfolios(db: Session, skip: int = 0, limit: int = 100) -> List[Portfolio]:
        """Get all portfolios with pagination"""
        return db.query(Portfolio).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_portfolio(db: Session, portfolio_data: Dict[str, Any]) -> Portfolio:
        """Create a new portfolio"""
        db_portfolio = Portfolio(**portfolio_data)
        db.add(db_portfolio)
        db.commit()
        db.refresh(db_portfolio)
        return db_portfolio
    
    @staticmethod
    def update_portfolio(db: Session, portfolio_id: int, portfolio_data: Dict[str, Any]) -> Optional[Portfolio]:
        """Update an existing portfolio"""
        db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id)
        if db_portfolio:
            for key, value in portfolio_data.items():
                setattr(db_portfolio, key, value)
            db.commit()
            db.refresh(db_portfolio)
        return db_portfolio
    
    @staticmethod
    def delete_portfolio(db: Session, portfolio_id: int) -> bool:
        """Delete a portfolio by ID"""
        db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id)
        if db_portfolio:
            db.delete(db_portfolio)
            db.commit()
            return True
        return False
    
    # Portfolio Strategy methods
    @staticmethod
    def get_portfolio_strategies(db: Session, portfolio_id: int) -> List[PortfolioStrategy]:
        """Get all strategies in a portfolio"""
        return db.query(PortfolioStrategy).filter(PortfolioStrategy.portfolio_id == portfolio_id).all()
    
    @staticmethod
    def add_strategy_to_portfolio(db: Session, portfolio_id: int, strategy_id: int, allocation: float = 0.0) -> PortfolioStrategy:
        """Add a strategy to a portfolio with allocation"""
        db_portfolio_strategy = PortfolioStrategy(
            portfolio_id=portfolio_id,
            strategy_id=strategy_id,
            allocation=allocation
        )
        db.add(db_portfolio_strategy)
        db.commit()
        db.refresh(db_portfolio_strategy)
        return db_portfolio_strategy
    
    @staticmethod
    def update_strategy_allocation(db: Session, portfolio_id: int, strategy_id: int, allocation: float) -> Optional[PortfolioStrategy]:
        """Update the allocation of a strategy in a portfolio"""
        db_portfolio_strategy = db.query(PortfolioStrategy).filter(
            PortfolioStrategy.portfolio_id == portfolio_id,
            PortfolioStrategy.strategy_id == strategy_id
        ).first()
        
        if db_portfolio_strategy:
            db_portfolio_strategy.allocation = allocation
            db_portfolio_strategy.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_portfolio_strategy)
        
        return db_portfolio_strategy
    
    @staticmethod
    def remove_strategy_from_portfolio(db: Session, portfolio_id: int, strategy_id: int) -> bool:
        """Remove a strategy from a portfolio"""
        db_portfolio_strategy = db.query(PortfolioStrategy).filter(
            PortfolioStrategy.portfolio_id == portfolio_id,
            PortfolioStrategy.strategy_id == strategy_id
        ).first()
        
        if db_portfolio_strategy:
            db.delete(db_portfolio_strategy)
            db.commit()
            return True
        
        return False
    
    # Portfolio Asset methods
    @staticmethod
    def get_portfolio_assets(db: Session, portfolio_id: int) -> List[PortfolioAsset]:
        """Get all assets in a portfolio"""
        return db.query(PortfolioAsset).filter(PortfolioAsset.portfolio_id == portfolio_id).all()
    
    @staticmethod
    def get_portfolio_asset(db: Session, portfolio_id: int, asset_id: int) -> Optional[PortfolioAsset]:
        """Get a specific asset in a portfolio"""
        return db.query(PortfolioAsset).filter(
            PortfolioAsset.portfolio_id == portfolio_id,
            PortfolioAsset.asset_id == asset_id
        ).first()
    
    @staticmethod
    def add_asset_to_portfolio(db: Session, portfolio_asset_data: Dict[str, Any]) -> PortfolioAsset:
        """Add an asset to a portfolio"""
        db_portfolio_asset = PortfolioAsset(**portfolio_asset_data)
        db.add(db_portfolio_asset)
        db.commit()
        db.refresh(db_portfolio_asset)
        return db_portfolio_asset
    
    @staticmethod
    def update_portfolio_asset(db: Session, portfolio_id: int, asset_id: int, 
                              update_data: Dict[str, Any]) -> Optional[PortfolioAsset]:
        """Update a portfolio asset"""
        db_portfolio_asset = PortfolioRepository.get_portfolio_asset(db, portfolio_id, asset_id)
        
        if db_portfolio_asset:
            for key, value in update_data.items():
                setattr(db_portfolio_asset, key, value)
            
            db_portfolio_asset.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_portfolio_asset)
        
        return db_portfolio_asset
    
    # Performance Metrics methods
    @staticmethod
    def get_performance_metrics(db: Session, portfolio_id: int, 
                               start_date: Optional[datetime] = None, 
                               end_date: Optional[datetime] = None,
                               limit: int = 30) -> List[PerformanceMetric]:
        """Get performance metrics for a portfolio with date filtering"""
        query = db.query(PerformanceMetric).filter(PerformanceMetric.portfolio_id == portfolio_id)
        
        if start_date:
            query = query.filter(PerformanceMetric.timestamp >= start_date)
        
        if end_date:
            query = query.filter(PerformanceMetric.timestamp <= end_date)
        
        return query.order_by(PerformanceMetric.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def add_performance_metric(db: Session, metric_data: Dict[str, Any]) -> PerformanceMetric:
        """Add a performance metric record"""
        db_metric = PerformanceMetric(**metric_data)
        db.add(db_metric)
        db.commit()
        db.refresh(db_metric)
        return db_metric
    
    # Trade methods
    @staticmethod
    def get_trades(db: Session, portfolio_id: int, 
                  start_date: Optional[datetime] = None, 
                  end_date: Optional[datetime] = None,
                  limit: int = 100) -> List[Trade]:
        """Get trades for a portfolio with date filtering"""
        query = db.query(Trade).filter(Trade.portfolio_id == portfolio_id)
        
        if start_date:
            query = query.filter(Trade.timestamp >= start_date)
        
        if end_date:
            query = query.filter(Trade.timestamp <= end_date)
        
        return query.order_by(Trade.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def add_trade(db: Session, trade_data: Dict[str, Any]) -> Trade:
        """Add a trade record"""
        db_trade = Trade(**trade_data)
        db.add(db_trade)
        db.commit()
        db.refresh(db_trade)
        return db_trade
    
    @staticmethod
    def update_trade(db: Session, trade_id: int, update_data: Dict[str, Any]) -> Optional[Trade]:
        """Update a trade record"""
        db_trade = db.query(Trade).filter(Trade.id == trade_id).first()
        
        if db_trade:
            for key, value in update_data.items():
                setattr(db_trade, key, value)
            
            db.commit()
            db.refresh(db_trade)
        
        return db_trade

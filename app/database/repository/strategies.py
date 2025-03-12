from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database.models import Strategy, StrategyOptimization

class StrategyRepository:
    """
    Repository for strategy-related database operations
    """
    
    @staticmethod
    def get_strategy(db: Session, strategy_id: int) -> Optional[Strategy]:
        """Get strategy by ID"""
        return db.query(Strategy).filter(Strategy.id == strategy_id).first()
    
    @staticmethod
    def get_strategy_by_name(db: Session, name: str) -> Optional[Strategy]:
        """Get strategy by name"""
        return db.query(Strategy).filter(Strategy.name == name).first()
    
    @staticmethod
    def get_strategies(db: Session, skip: int = 0, limit: int = 100) -> List[Strategy]:
        """Get all strategies with pagination"""
        return db.query(Strategy).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_strategies_by_asset_class(db: Session, asset_class_id: int) -> List[Strategy]:
        """Get all strategies for a specific asset class"""
        return db.query(Strategy).filter(Strategy.asset_class_id == asset_class_id).all()
    
    @staticmethod
    def create_strategy(db: Session, strategy_data: Dict[str, Any]) -> Strategy:
        """Create a new strategy"""
        db_strategy = Strategy(**strategy_data)
        db.add(db_strategy)
        db.commit()
        db.refresh(db_strategy)
        return db_strategy
    
    @staticmethod
    def update_strategy(db: Session, strategy_id: int, strategy_data: Dict[str, Any]) -> Optional[Strategy]:
        """Update an existing strategy"""
        db_strategy = StrategyRepository.get_strategy(db, strategy_id)
        if db_strategy:
            for key, value in strategy_data.items():
                setattr(db_strategy, key, value)
            db.commit()
            db.refresh(db_strategy)
        return db_strategy
    
    @staticmethod
    def delete_strategy(db: Session, strategy_id: int) -> bool:
        """Delete a strategy by ID"""
        db_strategy = StrategyRepository.get_strategy(db, strategy_id)
        if db_strategy:
            db.delete(db_strategy)
            db.commit()
            return True
        return False
    
    # Strategy Optimization methods
    @staticmethod
    def get_strategy_optimization(db: Session, optimization_id: int) -> Optional[StrategyOptimization]:
        """Get strategy optimization by ID"""
        return db.query(StrategyOptimization).filter(StrategyOptimization.id == optimization_id).first()
    
    @staticmethod
    def get_strategy_optimizations(db: Session, strategy_id: int, limit: int = 10) -> List[StrategyOptimization]:
        """Get recent optimizations for a strategy"""
        return db.query(StrategyOptimization).\
            filter(StrategyOptimization.strategy_id == strategy_id).\
            order_by(StrategyOptimization.timestamp.desc()).\
            limit(limit).all()
    
    @staticmethod
    def create_strategy_optimization(db: Session, optimization_data: Dict[str, Any]) -> StrategyOptimization:
        """Create a new strategy optimization record"""
        db_optimization = StrategyOptimization(**optimization_data)
        db.add(db_optimization)
        db.commit()
        db.refresh(db_optimization)
        return db_optimization
    
    @staticmethod
    def get_latest_strategy_optimization(db: Session, strategy_id: int) -> Optional[StrategyOptimization]:
        """Get the latest optimization for a strategy"""
        return db.query(StrategyOptimization).\
            filter(StrategyOptimization.strategy_id == strategy_id).\
            order_by(StrategyOptimization.timestamp.desc()).\
            first()

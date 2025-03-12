from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.database.session import Base

class AssetClass(Base):
    """
    Asset class model (e.g., ETFs, commodities, bonds)
    """
    __tablename__ = "asset_classes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    assets = relationship("Asset", back_populates="asset_class")


class Asset(Base):
    """
    Asset model (specific tradable instruments)
    """
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    name = Column(String)
    asset_class_id = Column(Integer, ForeignKey("asset_classes.id"))
    yfinance_symbol = Column(String)  # Symbol used with yfinance
    alpaca_symbol = Column(String)    # Symbol used with Alpaca
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    asset_class = relationship("AssetClass", back_populates="assets")
    portfolio_assets = relationship("PortfolioAsset", back_populates="asset")
    optimizations = relationship("AssetOptimization", back_populates="asset")
    market_data = relationship("MarketData", back_populates="asset")


class Strategy(Base):
    """
    Strategy model (trading/investment strategy)
    """
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    asset_class_id = Column(Integer, ForeignKey("asset_classes.id"))
    parameters = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    asset_class = relationship("AssetClass")
    portfolio_strategies = relationship("PortfolioStrategy", back_populates="strategy")
    optimizations = relationship("StrategyOptimization", back_populates="strategy")


class Portfolio(Base):
    """
    Portfolio model (collection of strategies)
    """
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    initial_capital = Column(Float, default=10000.0)
    current_value = Column(Float)
    risk_tolerance = Column(Float, default=0.5)  # 0-1 scale
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    portfolio_strategies = relationship("PortfolioStrategy", back_populates="portfolio")
    portfolio_assets = relationship("PortfolioAsset", back_populates="portfolio")
    performance_metrics = relationship("PerformanceMetric", back_populates="portfolio")
    trades = relationship("Trade", back_populates="portfolio")


class PortfolioStrategy(Base):
    """
    Many-to-many relationship between portfolios and strategies
    """
    __tablename__ = "portfolio_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    allocation = Column(Float, default=0.0)  # Percentage allocation (0-1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    portfolio = relationship("Portfolio", back_populates="portfolio_strategies")
    strategy = relationship("Strategy", back_populates="portfolio_strategies")


class PortfolioAsset(Base):
    """
    Portfolio holdings (actual positions)
    """
    __tablename__ = "portfolio_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"))
    quantity = Column(Float, default=0.0)
    average_price = Column(Float)
    current_price = Column(Float)
    target_allocation = Column(Float, default=0.0)
    current_allocation = Column(Float, default=0.0)
    last_rebalanced = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    portfolio = relationship("Portfolio", back_populates="portfolio_assets")
    asset = relationship("Asset", back_populates="portfolio_assets")


class MarketData(Base):
    """
    Market data storage
    """
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"))
    timestamp = Column(DateTime, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    asset = relationship("Asset", back_populates="market_data")


class AssetOptimization(Base):
    """
    Asset optimization results
    """
    __tablename__ = "asset_optimizations"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"))
    parameters = Column(JSON)
    metrics = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    asset = relationship("Asset", back_populates="optimizations")


class StrategyOptimization(Base):
    """
    Strategy optimization results
    """
    __tablename__ = "strategy_optimizations"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    parameters = Column(JSON)
    metrics = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    strategy = relationship("Strategy", back_populates="optimizations")


class PerformanceMetric(Base):
    """
    Performance metrics for portfolios
    """
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_return = Column(Float)
    daily_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    volatility = Column(Float)
    win_rate = Column(Float)
    additional_metrics = Column(JSON, default={})
    
    portfolio = relationship("Portfolio", back_populates="performance_metrics")


class Trade(Base):
    """
    Trade execution records
    """
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    order_type = Column(String)  # market, limit, etc.
    side = Column(String)  # buy or sell
    quantity = Column(Float)
    price = Column(Float)
    status = Column(String)  # pending, filled, canceled, etc.
    broker_order_id = Column(String)  # Order ID in Alpaca/broker
    trade_costs = Column(Float, default=0.0)
    notes = Column(String)
    
    portfolio = relationship("Portfolio", back_populates="trades")
    asset = relationship("Asset")

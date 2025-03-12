from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel, constr, confloat, conint
from datetime import datetime, date

from app.database.session import get_db
from app.database.repository.portfolios import PortfolioRepository
from app.database.repository.strategies import StrategyRepository
from app.database.repository.assets import AssetRepository
from app.services.portfolio_service import PortfolioService
from app.services.allocation_service import AllocationService
from app.services.execution_service import ExecutionService

router = APIRouter()

# Pydantic models for request/response
class PortfolioBase(BaseModel):
    name: constr(min_length=1, max_length=100)
    description: Optional[str] = None
    initial_capital: confloat(gt=0.0) = 10000.0
    risk_tolerance: confloat(ge=0.0, le=1.0) = 0.5
    is_active: bool = True

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=100)] = None
    description: Optional[str] = None
    initial_capital: Optional[confloat(gt=0.0)] = None
    risk_tolerance: Optional[confloat(ge=0.0, le=1.0)] = None
    is_active: Optional[bool] = None

class PortfolioResponse(PortfolioBase):
    id: int
    current_value: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class PortfolioStrategyBase(BaseModel):
    strategy_id: int
    allocation: confloat(ge=0.0, le=1.0)

class PortfolioStrategyCreate(PortfolioStrategyBase):
    pass

class PortfolioStrategyUpdate(BaseModel):
    allocation: confloat(ge=0.0, le=1.0)

class PortfolioStrategyResponse(PortfolioStrategyBase):
    id: int
    portfolio_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class PortfolioAssetBase(BaseModel):
    asset_id: int
    quantity: float = 0.0
    target_allocation: confloat(ge=0.0, le=1.0) = 0.0

class PortfolioAssetCreate(PortfolioAssetBase):
    pass

class PortfolioAssetUpdate(BaseModel):
    quantity: Optional[float] = None
    target_allocation: Optional[confloat(ge=0.0, le=1.0)] = None

class PortfolioAssetResponse(BaseModel):
    id: int
    portfolio_id: int
    asset_id: int
    quantity: float
    average_price: Optional[float] = None
    current_price: Optional[float] = None
    target_allocation: float
    current_allocation: float
    last_rebalanced: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class PerformanceMetricResponse(BaseModel):
    id: int
    portfolio_id: int
    timestamp: datetime
    total_return: float
    daily_return: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    win_rate: float
    additional_metrics: Dict[str, Any] = {}
    
    class Config:
        orm_mode = True

class TradeBase(BaseModel):
    asset_id: int
    order_type: str
    side: str
    quantity: float
    price: Optional[float] = None

class TradeCreate(TradeBase):
    pass

class TradeResponse(BaseModel):
    id: int
    portfolio_id: int
    asset_id: int
    timestamp: datetime
    order_type: str
    side: str
    quantity: float
    price: Optional[float] = None
    status: str
    broker_order_id: Optional[str] = None
    trade_costs: float = 0.0
    notes: Optional[str] = None
    
    class Config:
        orm_mode = True

class RebalanceRequest(BaseModel):
    portfolio_id: int
    max_trades: Optional[int] = None
    trade_limit_pct: Optional[float] = None

# Portfolio endpoints
@router.get("/portfolios", response_model=List[PortfolioResponse])
def get_portfolios(
    skip: int = 0, 
    limit: int = 100, 
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all portfolios with pagination and filters"""
    portfolios = PortfolioRepository.get_portfolios(db, skip=skip, limit=limit)
    
    # Filter by active status if needed
    if is_active is not None:
        portfolios = [p for p in portfolios if p.is_active == is_active]
    
    return portfolios

@router.get("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(
    portfolio_id: int, 
    db: Session = Depends(get_db)
):
    """Get portfolio by ID"""
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return db_portfolio

@router.post("/portfolios", response_model=PortfolioResponse)
def create_portfolio(
    portfolio: PortfolioCreate, 
    db: Session = Depends(get_db)
):
    """Create a new portfolio"""
    # Check if portfolio with same name already exists
    db_portfolio = PortfolioRepository.get_portfolio_by_name(db, name=portfolio.name)
    if db_portfolio:
        raise HTTPException(status_code=400, detail="Portfolio with this name already exists")
    
    # Create portfolio with current value equal to initial capital
    portfolio_data = portfolio.dict()
    portfolio_data["current_value"] = portfolio_data["initial_capital"]
    
    return PortfolioRepository.create_portfolio(db=db, portfolio_data=portfolio_data)

@router.put("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: int, 
    portfolio: PortfolioUpdate, 
    db: Session = Depends(get_db)
):
    """Update an existing portfolio"""
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Filter out None values from update data
    update_data = {k: v for k, v in portfolio.dict().items() if v is not None}
    
    # If name is being updated, check for uniqueness
    if 'name' in update_data:
        name_check = PortfolioRepository.get_portfolio_by_name(db, name=update_data['name'])
        if name_check and name_check.id != portfolio_id:
            raise HTTPException(status_code=400, detail="Portfolio with this name already exists")
    
    return PortfolioRepository.update_portfolio(db=db, portfolio_id=portfolio_id, portfolio_data=update_data)

@router.delete("/portfolios/{portfolio_id}")
def delete_portfolio(
    portfolio_id: int, 
    db: Session = Depends(get_db)
):
    """Delete a portfolio by ID"""
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    success = PortfolioRepository.delete_portfolio(db=db, portfolio_id=portfolio_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete portfolio")
    
    return {"detail": "Portfolio deleted successfully"}

# Portfolio Strategies endpoints
@router.get("/portfolios/{portfolio_id}/strategies", response_model=List[PortfolioStrategyResponse])
def get_portfolio_strategies(
    portfolio_id: int, 
    db: Session = Depends(get_db)
):
    """Get all strategies in a portfolio"""
    # Check if portfolio exists
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return PortfolioRepository.get_portfolio_strategies(db, portfolio_id=portfolio_id)

@router.post("/portfolios/{portfolio_id}/strategies", response_model=PortfolioStrategyResponse)
def add_strategy_to_portfolio(
    portfolio_id: int, 
    portfolio_strategy: PortfolioStrategyCreate, 
    db: Session = Depends(get_db)
):
    """Add a strategy to a portfolio"""
    # Check if portfolio exists
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Check if strategy exists
    db_strategy = StrategyRepository.get_strategy(db, strategy_id=portfolio_strategy.strategy_id)
    if db_strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Check if strategy is already in portfolio
    db_portfolio_strategies = PortfolioRepository.get_portfolio_strategies(db, portfolio_id=portfolio_id)
    for ps in db_portfolio_strategies:
        if ps.strategy_id == portfolio_strategy.strategy_id:
            raise HTTPException(status_code=400, detail="Strategy is already in this portfolio")
    
    return PortfolioRepository.add_strategy_to_portfolio(
        db=db, 
        portfolio_id=portfolio_id, 
        strategy_id=portfolio_strategy.strategy_id, 
        allocation=portfolio_strategy.allocation
    )

@router.put("/portfolios/{portfolio_id}/strategies/{strategy_id}", response_model=PortfolioStrategyResponse)
def update_portfolio_strategy(
    portfolio_id: int, 
    strategy_id: int, 
    portfolio_strategy: PortfolioStrategyUpdate, 
    db: Session = Depends(get_db)
):
    """Update strategy allocation in a portfolio"""
    # Check if portfolio exists
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Check if strategy exists
    db_strategy = StrategyRepository.get_strategy(db, strategy_id=strategy_id)
    if db_strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Update the allocation
    result = PortfolioRepository.update_strategy_allocation(
        db=db, 
        portfolio_id=portfolio_id, 
        strategy_id=strategy_id, 
        allocation=portfolio_strategy.allocation
    )
    
    if result is None:
        raise HTTPException(status_code=404, detail="Strategy not found in this portfolio")
    
    return result

@router.delete("/portfolios/{portfolio_id}/strategies/{strategy_id}")
def remove_strategy_from_portfolio(
    portfolio_id: int, 
    strategy_id: int, 
    db: Session = Depends(get_db)
):
    """Remove a strategy from a portfolio"""
    # Check if portfolio exists
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Check if strategy exists
    db_strategy = StrategyRepository.get_strategy(db, strategy_id=strategy_id)
    if db_strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Remove the strategy
    success = PortfolioRepository.remove_strategy_from_portfolio(
        db=db, 
        portfolio_id=portfolio_id, 
        strategy_id=strategy_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found in this portfolio")
    
    return {"detail": "Strategy removed from portfolio successfully"}

# Portfolio Assets endpoints
@router.get("/portfolios/{portfolio_id}/assets", response_model=List[PortfolioAssetResponse])
def get_portfolio_assets(
    portfolio_id: int, 
    db: Session = Depends(get_db)
):
    """Get all assets in a portfolio"""
    # Check if portfolio exists
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return PortfolioRepository.get_portfolio_assets(db, portfolio_id=portfolio_id)

@router.post("/portfolios/{portfolio_id}/assets", response_model=PortfolioAssetResponse)
def add_asset_to_portfolio(
    portfolio_id: int, 
    portfolio_asset: PortfolioAssetCreate, 
    db: Session = Depends(get_db)
):
    """Add an asset to a portfolio"""
    # Check if portfolio exists
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Check if asset exists
    db_asset = AssetRepository.get_asset(db, asset_id=portfolio_asset.asset_id)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Check if asset is already in portfolio
    db_portfolio_asset = PortfolioRepository.get_portfolio_asset(db, portfolio_id=portfolio_id, asset_id=portfolio_asset.asset_id)
    if db_portfolio_asset:
        raise HTTPException(status_code=400, detail="Asset is already in this portfolio")
    
    # Create portfolio asset data
    portfolio_asset_data = portfolio_asset.dict()
    portfolio_asset_data["portfolio_id"] = portfolio_id
    portfolio_asset_data["current_allocation"] = 0.0  # Initialize with zero allocation
    
    return PortfolioRepository.add_asset_to_portfolio(db=db, portfolio_asset_data=portfolio_asset_data)

@router.put("/portfolios/{portfolio_id}/assets/{asset_id}", response_model=PortfolioAssetResponse)
def update_portfolio_asset(
    portfolio_id: int, 
    asset_id: int, 
    portfolio_asset: PortfolioAssetUpdate, 
    db: Session = Depends(get_db)
):
    """Update an asset in a portfolio"""
    # Check if portfolio exists
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Check if asset exists
    db_asset = AssetRepository.get_asset(db, asset_id=asset_id)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Filter out None values from update data
    update_data = {k: v for k, v in portfolio_asset.dict().items() if v is not None}
    
    # Update the asset
    result = PortfolioRepository.update_portfolio_asset(
        db=db, 
        portfolio_id=portfolio_id, 
        asset_id=asset_id, 
        update_data=update_data
    )
    
    if result is None:
        raise HTTPException(status_code=404, detail="Asset not found in this portfolio")
    
    return result

# Performance endpoints
@router.get("/portfolios/{portfolio_id}/performance", response_model=List[PerformanceMetricResponse])
def get_portfolio_performance(
    portfolio_id: int, 
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get performance metrics for a portfolio"""
    # Check if portfolio exists
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Convert dates to datetime if provided
    start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
    end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
    
    return PortfolioRepository.get_performance_metrics(
        db=db, 
        portfolio_id=portfolio_id, 
        start_date=start_datetime, 
        end_date=end_datetime,
        limit=limit
    )

# Trade endpoints
@router.get("/portfolios/{portfolio_id}/trades", response_model=List[TradeResponse])
def get_portfolio_trades(
    portfolio_id: int, 
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get trades for a portfolio"""
    # Check if portfolio exists
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Convert dates to datetime if provided
    start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
    end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
    
    return PortfolioRepository.get_trades(
        db=db, 
        portfolio_id=portfolio_id, 
        start_date=start_datetime, 
        end_date=end_datetime,
        limit=limit
    )

@router.post("/portfolios/{portfolio_id}/trades", response_model=TradeResponse)
def create_trade(
    portfolio_id: int, 
    trade: TradeCreate, 
    db: Session = Depends(get_db)
):
    """Create a new trade for a portfolio"""
    # Check if portfolio exists
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Check if asset exists
    db_asset = AssetRepository.get_asset(db, asset_id=trade.asset_id)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Prepare trade data
    trade_data = trade.dict()
    trade_data["portfolio_id"] = portfolio_id
    trade_data["timestamp"] = datetime.utcnow()
    trade_data["status"] = "pending"
    
    # Create the trade record
    db_trade = PortfolioRepository.add_trade(db=db, trade_data=trade_data)
    
    # Execute the trade (in a real system, this would typically be a background task)
    execution_service = ExecutionService()
    try:
        executed_trade = execution_service.execute_trade(db=db, trade_id=db_trade.id)
        return executed_trade
    except Exception as e:
        # Update trade status to failed
        PortfolioRepository.update_trade(db=db, trade_id=db_trade.id, update_data={"status": "failed", "notes": str(e)})
        raise HTTPException(status_code=500, detail=f"Trade execution failed: {str(e)}")

@router.post("/portfolios/{portfolio_id}/rebalance")
def rebalance_portfolio(
    portfolio_id: int, 
    rebalance_request: RebalanceRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Rebalance a portfolio based on target allocations"""
    # Check if portfolio exists
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Initialize portfolio service
    portfolio_service = PortfolioService()
    
    # Start rebalancing in background
    task_id = f"rebalance_portfolio_{portfolio_id}_{datetime.utcnow().timestamp()}"
    background_tasks.add_task(
        portfolio_service.rebalance_portfolio,
        db=db,
        portfolio_id=portfolio_id,
        max_trades=rebalance_request.max_trades,
        trade_limit_pct=rebalance_request.trade_limit_pct,
        task_id=task_id
    )
    
    # Return immediately with task ID
    return {
        "portfolio_id": portfolio_id,
        "task_id": task_id,
        "status": "started",
        "message": "Portfolio rebalancing started in the background"
    }

@router.post("/portfolios/{portfolio_id}/optimize-allocation")
def optimize_allocation(
    portfolio_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Optimize strategy allocations for a portfolio"""
    # Check if portfolio exists
    db_portfolio = PortfolioRepository.get_portfolio(db, portfolio_id=portfolio_id)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Check if portfolio has any strategies
    portfolio_strategies = PortfolioRepository.get_portfolio_strategies(db, portfolio_id=portfolio_id)
    if not portfolio_strategies:
        raise HTTPException(status_code=400, detail="Portfolio has no strategies to optimize")
    
    # Initialize allocation service
    allocation_service = AllocationService()
    
    # Start allocation optimization in background
    task_id = f"optimize_allocation_{portfolio_id}_{datetime.utcnow().timestamp()}"
    background_tasks.add_task(
        allocation_service.optimize_allocation,
        db=db,
        portfolio_id=portfolio_id,
        task_id=task_id
    )
    
    # Return immediately with task ID
    return {
        "portfolio_id": portfolio_id,
        "task_id": task_id,
        "status": "started",
        "message": "Portfolio allocation optimization started in the background"
    }

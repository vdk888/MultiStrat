from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database.session import get_db
from app.database.repository.assets import AssetRepository
from app.database.repository.strategies import StrategyRepository
from app.services.optimization_service import OptimizationService

router = APIRouter()

# Pydantic models for request/response
class OptimizationBase(BaseModel):
    strategy_id: int
    parameters: Optional[Dict[str, Any]] = None
    objective: str = "sharpe_ratio"  # Default objective function

class OptimizationCreate(OptimizationBase):
    pass

class OptimizationResponse(BaseModel):
    id: int
    strategy_id: int
    parameters: Dict[str, Any]
    metrics: Dict[str, Any]
    timestamp: datetime
    
    class Config:
        orm_mode = True

class OptimizationStatus(BaseModel):
    strategy_id: int
    status: str
    progress: float
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None

class OptimizationRequest(BaseModel):
    strategy_id: int
    asset_ids: List[int]
    parameters: Optional[Dict[str, Any]] = None
    objective: str = "sharpe_ratio"
    days: int = 30
    
# Optimization endpoints
@router.post("/optimize", response_model=OptimizationStatus)
def start_optimization(
    optimization: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a new optimization in the background"""
    # Check if strategy exists
    db_strategy = StrategyRepository.get_strategy(db, strategy_id=optimization.strategy_id)
    if db_strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Check if assets exist
    assets = []
    for asset_id in optimization.asset_ids:
        db_asset = AssetRepository.get_asset(db, asset_id=asset_id)
        if db_asset is None:
            raise HTTPException(status_code=404, detail=f"Asset with ID {asset_id} not found")
        assets.append(db_asset)
    
    # Initialize optimization service
    optimization_service = OptimizationService()
    
    # Start optimization in background
    task_id = f"optimize_strategy_{optimization.strategy_id}_{datetime.utcnow().timestamp()}"
    background_tasks.add_task(
        optimization_service.run_optimization,
        db=db,
        strategy_id=optimization.strategy_id,
        asset_ids=optimization.asset_ids,
        parameters=optimization.parameters,
        objective=optimization.objective,
        days=optimization.days,
        task_id=task_id
    )
    
    # Return immediately with task status
    return {
        "strategy_id": optimization.strategy_id,
        "status": "started",
        "progress": 0.0,
        "started_at": datetime.utcnow(),
        "finished_at": None,
        "error": None
    }

@router.get("/optimize/status/{task_id}", response_model=OptimizationStatus)
def get_optimization_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get the status of an optimization task"""
    optimization_service = OptimizationService()
    status = optimization_service.get_optimization_status(task_id)
    
    if status is None:
        raise HTTPException(status_code=404, detail="Optimization task not found")
    
    return status

@router.get("/optimize/results/{strategy_id}", response_model=List[OptimizationResponse])
def get_optimization_results(
    strategy_id: int,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get optimization results for a strategy"""
    # Check if strategy exists
    db_strategy = StrategyRepository.get_strategy(db, strategy_id=strategy_id)
    if db_strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Get optimization results
    results = StrategyRepository.get_strategy_optimizations(db, strategy_id=strategy_id, limit=limit)
    return results

@router.get("/optimize/latest/{strategy_id}", response_model=OptimizationResponse)
def get_latest_optimization(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """Get the latest optimization result for a strategy"""
    # Check if strategy exists
    db_strategy = StrategyRepository.get_strategy(db, strategy_id=strategy_id)
    if db_strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Get latest optimization
    result = StrategyRepository.get_latest_strategy_optimization(db, strategy_id=strategy_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No optimization results found for this strategy")
    
    return result

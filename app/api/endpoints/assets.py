from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database.session import get_db
from app.database.repository.assets import AssetRepository
from app.services.data_service import DataService

router = APIRouter()

# Pydantic models for request/response
class AssetClassBase(BaseModel):
    name: str
    description: Optional[str] = None

class AssetClassCreate(AssetClassBase):
    pass

class AssetClassResponse(AssetClassBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class AssetBase(BaseModel):
    symbol: str
    name: str
    asset_class_id: int
    yfinance_symbol: Optional[str] = None
    alpaca_symbol: Optional[str] = None
    is_active: bool = True

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_class_id: Optional[int] = None
    yfinance_symbol: Optional[str] = None
    alpaca_symbol: Optional[str] = None
    is_active: Optional[bool] = None

class AssetResponse(AssetBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# Asset Class endpoints
@router.get("/asset-classes", response_model=List[AssetClassResponse])
def get_asset_classes(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Get all asset classes"""
    asset_classes = AssetRepository.get_asset_classes(db, skip=skip, limit=limit)
    return asset_classes

@router.post("/asset-classes", response_model=AssetClassResponse)
def create_asset_class(
    asset_class: AssetClassCreate, 
    db: Session = Depends(get_db)
):
    """Create a new asset class"""
    db_asset_class = AssetRepository.get_asset_class_by_name(db, name=asset_class.name)
    if db_asset_class:
        raise HTTPException(status_code=400, detail="Asset class already exists")
    return AssetRepository.create_asset_class(db=db, asset_class_data=asset_class.dict())

# Asset endpoints
@router.get("/assets", response_model=List[AssetResponse])
def get_assets(
    skip: int = 0, 
    limit: int = 100, 
    asset_class_id: Optional[int] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """Get all assets with optional filtering"""
    if asset_class_id:
        assets = AssetRepository.get_assets_by_class(db, asset_class_id=asset_class_id)
    else:
        assets = AssetRepository.get_assets(db, skip=skip, limit=limit)
    
    # Filter by active status if needed
    if is_active is not None:
        assets = [asset for asset in assets if asset.is_active == is_active]
    
    return assets

@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: int, 
    db: Session = Depends(get_db)
):
    """Get asset by ID"""
    db_asset = AssetRepository.get_asset(db, asset_id=asset_id)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset

@router.post("/assets", response_model=AssetResponse)
def create_asset(
    asset: AssetCreate, 
    db: Session = Depends(get_db)
):
    """Create a new asset"""
    # Check if asset already exists
    db_asset = AssetRepository.get_asset_by_symbol(db, symbol=asset.symbol)
    if db_asset:
        raise HTTPException(status_code=400, detail="Asset already exists")
    
    # Check if asset class exists
    db_asset_class = AssetRepository.get_asset_class(db, asset_class_id=asset.asset_class_id)
    if not db_asset_class:
        raise HTTPException(status_code=404, detail="Asset class not found")
    
    return AssetRepository.create_asset(db=db, asset_data=asset.dict())

@router.put("/assets/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: int, 
    asset: AssetUpdate, 
    db: Session = Depends(get_db)
):
    """Update an existing asset"""
    db_asset = AssetRepository.get_asset(db, asset_id=asset_id)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Filter out None values from update data
    update_data = {k: v for k, v in asset.dict().items() if v is not None}
    
    # If asset_class_id is provided, check that it exists
    if 'asset_class_id' in update_data:
        db_asset_class = AssetRepository.get_asset_class(db, asset_class_id=update_data['asset_class_id'])
        if not db_asset_class:
            raise HTTPException(status_code=404, detail="Asset class not found")
    
    return AssetRepository.update_asset(db=db, asset_id=asset_id, asset_data=update_data)

@router.delete("/assets/{asset_id}")
def delete_asset(
    asset_id: int, 
    db: Session = Depends(get_db)
):
    """Delete an asset by ID"""
    db_asset = AssetRepository.get_asset(db, asset_id=asset_id)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    success = AssetRepository.delete_asset(db=db, asset_id=asset_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete asset")
    
    return {"detail": "Asset deleted successfully"}

@router.get("/assets/{asset_id}/market-data")
def get_asset_market_data(
    asset_id: int,
    days: int = Query(30, ge=1, le=365),
    interval: str = Query("1d", regex="^(1m|5m|15m|30m|1h|1d|1wk|1mo)$"),
    db: Session = Depends(get_db)
):
    """Get market data for an asset"""
    # Check if asset exists
    db_asset = AssetRepository.get_asset(db, asset_id=asset_id)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Use data service to fetch market data
    data_service = DataService()
    try:
        market_data = data_service.get_historical_data(
            symbol=db_asset.yfinance_symbol or db_asset.symbol,
            days=days,
            interval=interval
        )
        return {
            "asset_id": asset_id,
            "symbol": db_asset.symbol,
            "interval": interval,
            "days": days,
            "data": market_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market data: {str(e)}")

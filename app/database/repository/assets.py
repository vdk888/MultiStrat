from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.models import Asset, AssetClass

class AssetRepository:
    """
    Repository for asset-related database operations
    """
    
    @staticmethod
    def get_asset(db: Session, asset_id: int) -> Optional[Asset]:
        """Get asset by ID"""
        return db.query(Asset).filter(Asset.id == asset_id).first()
    
    @staticmethod
    def get_asset_by_symbol(db: Session, symbol: str) -> Optional[Asset]:
        """Get asset by symbol"""
        return db.query(Asset).filter(Asset.symbol == symbol).first()
    
    @staticmethod
    def get_assets(db: Session, skip: int = 0, limit: int = 100) -> List[Asset]:
        """Get all assets with pagination"""
        return db.query(Asset).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_assets_by_class(db: Session, asset_class_id: int) -> List[Asset]:
        """Get all assets in a specific asset class"""
        return db.query(Asset).filter(Asset.asset_class_id == asset_class_id).all()
    
    @staticmethod
    def create_asset(db: Session, asset_data: dict) -> Asset:
        """Create a new asset"""
        db_asset = Asset(**asset_data)
        db.add(db_asset)
        db.commit()
        db.refresh(db_asset)
        return db_asset
    
    @staticmethod
    def update_asset(db: Session, asset_id: int, asset_data: dict) -> Optional[Asset]:
        """Update an existing asset"""
        db_asset = AssetRepository.get_asset(db, asset_id)
        if db_asset:
            for key, value in asset_data.items():
                setattr(db_asset, key, value)
            db.commit()
            db.refresh(db_asset)
        return db_asset
    
    @staticmethod
    def delete_asset(db: Session, asset_id: int) -> bool:
        """Delete an asset by ID"""
        db_asset = AssetRepository.get_asset(db, asset_id)
        if db_asset:
            db.delete(db_asset)
            db.commit()
            return True
        return False
    
    # Asset Class methods
    @staticmethod
    def get_asset_class(db: Session, asset_class_id: int) -> Optional[AssetClass]:
        """Get asset class by ID"""
        return db.query(AssetClass).filter(AssetClass.id == asset_class_id).first()
    
    @staticmethod
    def get_asset_classes(db: Session, skip: int = 0, limit: int = 100) -> List[AssetClass]:
        """Get all asset classes with pagination"""
        return db.query(AssetClass).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_asset_class(db: Session, asset_class_data: dict) -> AssetClass:
        """Create a new asset class"""
        db_asset_class = AssetClass(**asset_class_data)
        db.add(db_asset_class)
        db.commit()
        db.refresh(db_asset_class)
        return db_asset_class

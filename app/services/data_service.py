import pandas as pd
import numpy as np
import yfinance as yf
import logging
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.database.repository.assets import AssetRepository
from app.database.models import MarketData, Asset

# Set up logger
logger = logging.getLogger(__name__)

class DataService:
    """
    Service for fetching and managing market data
    """
    
    def __init__(self):
        """Initialize the data service"""
        self.settings = get_settings()
        self.default_interval = self.settings.DEFAULT_INTERVAL
        self.default_lookback_days = self.settings.DEFAULT_LOOKBACK_DAYS
    
    def get_historical_data(self, symbol: str, days: int = 30, interval: str = None) -> pd.DataFrame:
        """
        Fetch historical market data from Yahoo Finance
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'BTC-USD')
            days: Number of days of historical data to fetch
            interval: Data interval (e.g., '1d', '1h', '5m')
            
        Returns:
            DataFrame with historical market data
        """
        interval = interval or self.default_interval
        end_date = datetime.now(pytz.UTC)
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"Fetching {interval} data for {symbol} from {start_date} to {end_date}")
        
        try:
            # Use yfinance to fetch data
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                logger.warning(f"No data retrieved for {symbol}")
                return pd.DataFrame()
            
            # Convert data to dict format for API response
            result = []
            for idx, row in data.iterrows():
                result.append({
                    'timestamp': idx.isoformat(),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': float(row['Volume']),
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise
    
    def update_market_data(self, db: Session, asset_id: int, symbol: str) -> bool:
        """
        Update market data for an asset in the database
        
        Args:
            db: Database session
            asset_id: Asset ID to update
            symbol: Trading symbol to fetch data for
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Get historical data
            data = self.get_historical_data(
                symbol=symbol,
                days=self.default_lookback_days,
                interval=self.default_interval
            )
            
            if not data:
                logger.warning(f"No data to update for asset ID {asset_id}")
                return False
            
            # Get existing data timestamps to avoid duplicates
            existing_timestamps = set()
            existing_data = db.query(MarketData.timestamp).filter(MarketData.asset_id == asset_id).all()
            for record in existing_data:
                existing_timestamps.add(record[0].isoformat())
            
            # Add new data
            count = 0
            for record in data:
                if record['timestamp'] not in existing_timestamps:
                    timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                    db_record = MarketData(
                        asset_id=asset_id,
                        timestamp=timestamp,
                        open=record['open'],
                        high=record['high'],
                        low=record['low'],
                        close=record['close'],
                        volume=record['volume'],
                        created_at=datetime.utcnow()
                    )
                    db.add(db_record)
                    count += 1
            
            # Commit changes
            db.commit()
            logger.info(f"Added {count} new market data records for asset ID {asset_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating market data for asset ID {asset_id}: {str(e)}")
            return False
    
    def get_market_data_for_assets(self, db: Session, asset_ids: List[int], days: int = 30) -> Dict[int, pd.DataFrame]:
        """
        Get market data for multiple assets from the database
        
        Args:
            db: Database session
            asset_ids: List of asset IDs to get data for
            days: Number of days of data to retrieve
            
        Returns:
            Dictionary mapping asset IDs to DataFrames
        """
        result = {}
        start_date = datetime.utcnow() - timedelta(days=days)
        
        try:
            for asset_id in asset_ids:
                # Get asset symbol for logging
                asset = db.query(Asset).filter(Asset.id == asset_id).first()
                symbol = asset.symbol if asset else f"ID:{asset_id}"
                
                # Query market data
                data = db.query(MarketData).filter(
                    MarketData.asset_id == asset_id,
                    MarketData.timestamp >= start_date
                ).order_by(MarketData.timestamp).all()
                
                if not data:
                    logger.warning(f"No market data found for asset {symbol} (ID: {asset_id})")
                    continue
                
                # Convert to DataFrame
                df_data = {
                    'timestamp': [record.timestamp for record in data],
                    'open': [record.open for record in data],
                    'high': [record.high for record in data],
                    'low': [record.low for record in data],
                    'close': [record.close for record in data],
                    'volume': [record.volume for record in data]
                }
                
                df = pd.DataFrame(df_data)
                df.set_index('timestamp', inplace=True)
                
                # Add to result
                result[asset_id] = df
                logger.info(f"Retrieved {len(df)} market data records for asset {symbol} (ID: {asset_id})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving market data for assets: {str(e)}")
            raise
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get current prices for multiple symbols
        
        Args:
            symbols: List of trading symbols
            
        Returns:
            Dictionary mapping symbols to current prices
        """
        result = {}
        
        try:
            # Use yfinance to get current prices
            tickers = yf.Tickers(' '.join(symbols))
            
            for symbol in symbols:
                try:
                    # Get last price from info
                    ticker_data = tickers.tickers[symbol].info
                    if 'regularMarketPrice' in ticker_data and ticker_data['regularMarketPrice'] is not None:
                        result[symbol] = ticker_data['regularMarketPrice']
                    else:
                        # Fallback to history
                        hist = tickers.tickers[symbol].history(period="1d")
                        if not hist.empty:
                            result[symbol] = float(hist['Close'].iloc[-1])
                        else:
                            logger.warning(f"No price data available for {symbol}")
                except Exception as e:
                    logger.error(f"Error getting price for {symbol}: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting current prices: {str(e)}")
            raise

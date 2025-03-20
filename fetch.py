import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
from config import TRADING_SYMBOLS, DEFAULT_INTERVAL, DEFAULT_INTERVAL_WEEKLY, default_interval_yahoo
import logging
import pytz
from config import lookback_days_param
import time
from functools import lru_cache
from ratelimit import limits, sleep_and_retry

logger = logging.getLogger(__name__)

# Yahoo Finance has a rate limit of approximately 2000 requests per hour per IP
# We'll be conservative and use 1800 requests per hour (1 request every 2 seconds)
CALLS_PER_HOUR = 1800
PERIOD = 3600  # 1 hour in seconds
MIN_INTERVAL = PERIOD / CALLS_PER_HOUR  # Minimum interval between requests

@sleep_and_retry
@limits(calls=CALLS_PER_HOUR, period=PERIOD)
@lru_cache(maxsize=100)
def _fetch_yahoo_data(symbol: str, start: datetime, end: datetime, interval: str) -> pd.DataFrame:
    """
    Rate-limited and cached function to fetch data from Yahoo Finance
    """
    ticker = yf.Ticker(symbol)
    return ticker.history(start=start, end=end, interval=interval)

def fetch_historical_data(symbol: str, interval: str = default_interval_yahoo, days: int = 3) -> pd.DataFrame:
    """
    Fetch historical data from Yahoo Finance with rate limiting and caching
    """
    yf_symbol = TRADING_SYMBOLS[symbol]['yfinance']
    end = datetime.now(pytz.UTC)
    start = end - timedelta(days=days)
    
    logger.debug(f"Attempting to fetch {interval} data for {symbol} ({yf_symbol})")
    
    # Use exponential backoff for retries
    max_retries = 3
    backoff_factor = 2
    for attempt in range(max_retries):
        try:
            df = _fetch_yahoo_data(yf_symbol, start, end, interval)
            if not df.empty:
                break
        except Exception as e:
            wait_time = (backoff_factor ** attempt) * MIN_INTERVAL
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Waiting {wait_time:.1f}s before retry")
            time.sleep(wait_time)
            if attempt == max_retries - 1:
                logger.error(f"Failed to fetch data for {symbol} after {max_retries} attempts")
                raise e
            continue

    if df.empty:
        raise ValueError(f"No data available for {symbol} ({yf_symbol})")

    # Ensure we have enough data
    min_required_bars = 700  # Minimum bars needed for weekly signals
    if len(df) < min_required_bars:
        logger.debug(f"Only {len(df)} bars found, fetching more data")
        start = end - timedelta(days=days + 2)
        df = _fetch_yahoo_data(yf_symbol, start, end, interval)
    
    # Clean and format the data
    df.columns = [col.lower() for col in df.columns]
    df = df[['open', 'high', 'low', 'close', 'volume']]
    
    # Add logging for data quality
    logger.info(f"Fetched {len(df)} bars of {interval} data for {symbol} ({yf_symbol})")
    logger.info(f"Date range: {df.index[0]} to {df.index[-1]}")
    
    return df

def get_latest_data(symbol: str, interval: str = default_interval_yahoo, limit: Optional[int] = None) -> pd.DataFrame:
    """
    Get the most recent data points
    
    Args:
        symbol: Stock symbol
        interval: Data interval
        limit: Number of data points to return (default: None = all available data)
    
    Returns:
        DataFrame with the most recent data points
    """
    # Get the correct interval from config
    config_interval = TRADING_SYMBOLS[symbol].get('interval', interval)
    
    try:
        # Fetch at least 3 days of data for proper weekly signal calculation
        df = fetch_historical_data(symbol, config_interval, days=lookback_days_param)
        
        # Filter for market hours
        market_hours = TRADING_SYMBOLS[symbol]['market_hours']
        if market_hours['start'] != '00:00' or market_hours['end'] != '23:59':
            # Convert index to market timezone
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC')
            market_tz = market_hours['timezone']
            df.index = df.index.tz_convert(market_tz)
            
            # Create time masks for market hours
            start_time = pd.Timestamp.strptime(market_hours['start'], '%H:%M').time()
            end_time = pd.Timestamp.strptime(market_hours['end'], '%H:%M').time()
            
            # Filter for market hours
            df = df[
                (df.index.time >= start_time) & 
                (df.index.time <= end_time) &
                (df.index.weekday < 5)  # Monday = 0, Friday = 4
            ]
        
        # Apply limit if specified
        if limit is not None:
            return df.tail(limit)
        return df
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        raise

def is_market_open(symbol: str = 'SPY') -> bool:
    """Check if market is currently open for the given symbol"""
    try:
        market_hours = TRADING_SYMBOLS[symbol]['market_hours']
        now = datetime.now(pytz.UTC)
        
        # For 24/7 markets
        if market_hours['start'] == '00:00' and market_hours['end'] == '23:59':
            return True
            
        # Convert current time to market timezone
        market_tz = market_hours['timezone']
        market_time = now.astimezone(pytz.timezone(market_tz))
        
        # Check if it's a weekday
        if market_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Parse market hours
        start_time = datetime.strptime(market_hours['start'], '%H:%M').time()
        end_time = datetime.strptime(market_hours['end'], '%H:%M').time()
        current_time = market_time.time()
        
        return start_time <= current_time <= end_time
        
    except Exception as e:
        logger.error(f"Error checking market hours for {symbol}: {str(e)}")
        return False

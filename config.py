import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pytz
import yfinance as yf

ALPACA_PAPER = True
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    raise ValueError("Alpaca API credentials not found in environment variables")

# Default trading parameters
DEFAULT_RISK_PERCENT = 0.95
DEFAULT_INTERVAL = '1D' # available intervals: 1min, 5min, 15min, 30min, 1h, 4h, 1d
DEFAULT_INTERVAL_WEEKLY = '1W'

default_interval_yahoo = '1D' # available intervals: 1m, 5m, 15m, 30m, 1h, 4h, 1d

# Bars per day for each interval
BARS_PER_DAY = {
    '1m': 1440,
    '5m': 288,
    '15m': 96,
    '30m': 48,
    '60m': 24,
    '1h': 24,
    '1D': 1
}

# Maximum data points per request
MAX_DATA_POINTS = 2000

# Calculate maximum number of days for a given interval
def get_max_days(interval: str) -> int:
    """
    Calculate maximum number of days for a given interval
    
    Args:
        interval: Data interval
    
    Returns:
        Maximum number of days
    """
    bars_per_day = BARS_PER_DAY.get(interval, 24)  # Default to 24 bars/day
    max_days = MAX_DATA_POINTS // bars_per_day
    if interval == '1h':
        return min(730, max_days)
    elif interval == '1D':
        return min(1825, max_days)  # Allow up to 5 years of daily data
    return min(60, max_days)

# Interval to maximum days mapping
INTERVAL_MAX_DAYS = {interval: get_max_days(interval) for interval in BARS_PER_DAY}

# Default backtest interval based on DEFAULT_INTERVAL
default_backtest_interval = INTERVAL_MAX_DAYS.get(DEFAULT_INTERVAL.replace('min', 'm')) if INTERVAL_MAX_DAYS.get(DEFAULT_INTERVAL.replace('min', 'm')) else 365 * 0.4  # Default to 2 years if no limit
lookback_days_param = default_backtest_interval/4

#1-minute interval: Maximum of 7 days of historical data.
#5-minute interval: Maximum of 60 days of historical data.
#15-minute interval: Maximum of 60 days of historical data.
#30-minute interval: Maximum of 60 days of historical data.
#1-hour interval: Maximum of 730 days (2 years) of historical data.
#Daily interval: No strict limit, can fetch data for the entire available history.





# Trading symbols configuration
TRADING_SYMBOLS = {
    # Group 1: Major US Equity Market Indices
    'SPY': {
        'name': 'SPDR S&P 500 ETF Trust',
        'market': 'US_EQUITY',
        'yfinance': 'SPY',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    
    'QQQ': {
        'name': 'Invesco QQQ Trust',
        'market': 'US_EQUITY',
        'yfinance': 'QQQ',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'DIA': {
        'name': 'SPDR Dow Jones Industrial Average ETF',
        'market': 'US_EQUITY',
        'yfinance': 'DIA',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'IWM': {
        'name': 'iShares Russell 2000 ETF',
        'market': 'US_EQUITY',
        'yfinance': 'IWM',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'VTI': {
        'name': 'Vanguard Total Stock Market ETF',
        'market': 'US_EQUITY',
        'yfinance': 'VTI',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'RSP': {
        'name': 'Invesco S&P 500 Equal Weight ETF',
        'market': 'US_EQUITY',
        'yfinance': 'RSP',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'IJH': {
        'name': 'iShares Core S&P Mid-Cap ETF',
        'market': 'US_EQUITY',
        'yfinance': 'IJH',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
   
    
    'VO': {
        'name': 'Vanguard Mid-Cap ETF',
        'market': 'US_EQUITY',
        'yfinance': 'VO',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'MAGS': {
        'name': 'Roundhill Magnificent Seven ETF',
        'market': 'US_EQUITY',
        'yfinance': 'MAGS',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    # Group 2: US Equity Styles
    'VUG': {
        'name': 'Vanguard Growth ETF',
        'market': 'US_EQUITY',
        'yfinance': 'VUG',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'VTV': {
        'name': 'Vanguard Value ETF',
        'market': 'US_EQUITY',
        'yfinance': 'VTV',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'SPLV': {
        'name': 'Invesco S&P 500 Low Volatility ETF',
        'market': 'US_EQUITY',
        'yfinance': 'SPLV',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'SPHQ': {
        'name': 'Invesco S&P 500 Quality ETF',
        'market': 'US_EQUITY',
        'yfinance': 'SPHQ',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'MOAT': {
        'name': 'VanEck Morningstar Wide Moat ETF',
        'market': 'US_EQUITY',
        'yfinance': 'MOAT',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'SPMO': {
        'name': 'Invesco S&P 500 Momentum ETF',
        'market': 'US_EQUITY',
        'yfinance': 'SPMO',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'COWZ': {
        'name': 'Pacer US Cash Cows 100 ETF',
        'market': 'US_EQUITY',
        'yfinance': 'COWZ',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    
    'IWN': {
        'name': 'iShares Russell 2000 Value ETF',
        'market': 'US_EQUITY',
        'yfinance': 'IWN',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'AVUV': {
        'name': 'Avantis U.S. Small Cap Value ETF',
        'market': 'US_EQUITY',
        'yfinance': 'AVUV',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'VOT': {
        'name': 'Vanguard Mid-Cap Growth ETF',
        'market': 'US_EQUITY',
        'yfinance': 'VOT',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
   

    # Group 3: US Sector ETFs
    'XLF': {
        'name': 'Financial Select Sector SPDR Fund',
        'market': 'US_EQUITY',
        'yfinance': 'XLF',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'XLK': {
        'name': 'Technology Select Sector SPDR Fund',
        'market': 'US_EQUITY',
        'yfinance': 'XLK',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'XLE': {
        'name': 'Energy Select Sector SPDR Fund',
        'market': 'US_EQUITY',
        'yfinance': 'XLE',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'XLV': {
        'name': 'Health Care Select Sector SPDR Fund',
        'market': 'US_EQUITY',
        'yfinance': 'XLV',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'XLI': {
        'name': 'Industrial Select Sector SPDR Fund',
        'market': 'US_EQUITY',
        'yfinance': 'XLI',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'XLP': {
        'name': 'Consumer Staples Select Sector SPDR Fund',
        'market': 'US_EQUITY',
        'yfinance': 'XLP',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'XLY': {
        'name': 'Consumer Discretionary Select Sector SPDR Fund',
        'market': 'US_EQUITY',
        'yfinance': 'XLY',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'XLU': {
        'name': 'Utilities Select Sector SPDR Fund',
        'market': 'US_EQUITY',
        'yfinance': 'XLU',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'XLC': {
        'name': 'Communication Services Select Sector SPDR Fund',
        'market': 'US_EQUITY',
        'yfinance': 'XLC',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'XLRE': {
        'name': 'Real Estate Select Sector SPDR Fund',
        'market': 'US_EQUITY',
        'yfinance': 'XLRE',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'KRE': {
        'name': 'SPDR S&P Regional Banking ETF',
        'market': 'US_EQUITY',
        'yfinance': 'KRE',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'SMH': {
        'name': 'VanEck Semiconductor ETF',
        'market': 'US_EQUITY',
        'yfinance': 'SMH',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    },
    'XOP': {
        'name': 'SPDR S&P Oil & Gas Exploration & Production ETF',
        'market': 'US_EQUITY',
        'yfinance': 'XOP',
        'interval': default_interval_yahoo,
        'market_hours': {
            'start': '00:00',
            'end': '23:59',
            'timezone': 'UTC'
        }
    }
}

# Trading costs configuration
TRADING_COSTS = {
    'DEFAULT': {
        'trading_fee': 0.001,  # 0.1% trading fee
        'spread': 0.006,  # 0.6% spread (bid-ask)
    },
    'CRYPTO': {
        'trading_fee': 0.003,  # 0.3% taker fee
        'spread': 0.002,  # 0.2% maker fee
    },
    'STOCK': {
        'trading_fee': 0.0005,  # 0.05% trading fee
        'spread': 0.001,  # 0.1% spread (bid-ask)
    }
}

param_grid = {
    'percent_increase_buy': [0.02],
    'percent_decrease_sell': [0.02],
    'sell_down_lim': [2.0],
    'sell_rolling_std': [20],
    'buy_up_lim': [-2.0],
    'buy_rolling_std': [20],
    'macd_fast': [12],
    'macd_slow': [26],
    'macd_signal': [9],
    'rsi_period': [14],
    'stochastic_k_period': [14],
    'stochastic_d_period': [3],
    'fractal_window': [50, 100, 150],
    'fractal_lags': [[5, 10, 20], [10, 20, 40], [15, 30, 60]],
    'reactivity': [0.8, 0.9, 1.0, 1.1, 1.2],
    'weights': [
        {'weekly_macd_weight': 0.1, 'weekly_rsi_weight': 0.1, 'weekly_stoch_weight': 0.1, 'weekly_complexity_weight': 0.7,'macd_weight': 0.1, 'rsi_weight': 0.1, 'stoch_weight': 0.1, 'complexity_weight': 0.7},
        {'weekly_macd_weight': 0.15, 'weekly_rsi_weight': 0.15, 'weekly_stoch_weight': 0.15, 'weekly_complexity_weight': 0.55,'macd_weight': 0.15, 'rsi_weight': 0.15, 'stoch_weight': 0.15, 'complexity_weight': 0.55},
        {'weekly_macd_weight': 0.2, 'weekly_rsi_weight': 0.2, 'weekly_stoch_weight': 0.2, 'weekly_complexity_weight': 0.4,'macd_weight': 0.2, 'rsi_weight': 0.2, 'stoch_weight': 0.2, 'complexity_weight': 0.4},
        {'weekly_macd_weight': 0.25, 'weekly_rsi_weight': 0.25, 'weekly_stoch_weight': 0.25, 'weekly_complexity_weight': 0.25,'macd_weight': 0.25, 'rsi_weight': 0.25, 'stoch_weight': 0.25, 'complexity_weight': 0.25},
        {'weekly_macd_weight': 0.3, 'weekly_rsi_weight': 0.3, 'weekly_stoch_weight': 0.3, 'weekly_complexity_weight': 0.1,'macd_weight': 0.3, 'rsi_weight': 0.3, 'stoch_weight': 0.3, 'complexity_weight': 0.1},
        {'weekly_macd_weight': 0.3, 'weekly_rsi_weight': 0.3, 'weekly_stoch_weight': 0.3, 'weekly_complexity_weight': 0.1,'macd_weight': 0.1, 'rsi_weight': 0.1, 'stoch_weight': 0.1, 'complexity_weight': 0.7},

    ]
}

def calculate_capital_multiplier(lookback_days=default_backtest_interval/2):
    """
    Calculate a dynamic capital multiplier based on asset performance.
    
    Args:
        lookback_days: Number of days to look back for performance calculation
        
    Returns:
        float: Capital multiplier between 0.5 and 3.0
    """
    try:
        # Default return if calculation fails
        default_multiplier = 1.5
        
        # Get end and start dates
        end_date = datetime.now(pytz.UTC)
        start_date = end_date - timedelta(days=lookback_days * 2)  # Double lookback for MA calculation
        
        # Collect daily performance data for all assets
        daily_performances = []
        
        for symbol, config in TRADING_SYMBOLS.items():
            try:
                # Get the yfinance symbol
                yf_symbol = config['yfinance']
                if '/' in yf_symbol:
                    yf_symbol = yf_symbol.replace('/', '-')
                
                # Fetch historical data
                ticker = yf.Ticker(yf_symbol)
                data = ticker.history(start=start_date, end=end_date, interval=default_interval_yahoo)
                
                if len(data) >= 10:  # Need enough data for meaningful calculation
                    # Calculate daily returns
                    data['return'] = data['Close'].pct_change() * 100  # as percentage
                    
                    # Add to our collection, dropping NaN values
                    returns = data['return'].dropna().values
                    if len(returns) > 0:
                        daily_performances.append(returns)
            except Exception as e:
                print(f"Error processing {symbol}: {str(e)}")
                continue
        
        if not daily_performances or len(daily_performances) < 3:
            return default_multiplier
        
        # Calculate average daily performance across all assets for each day
        # Pad or truncate arrays to ensure they have the same length
        min_length = min(len(perfs) for perfs in daily_performances)
        if min_length < 10:  # Need enough data points
            return default_multiplier
            
        aligned_performances = [perfs[-min_length:] for perfs in daily_performances]
        daily_avg_performance = np.mean(aligned_performances, axis=0)
        
        # Calculate moving average with a window of 7 days
        window = min(7, len(daily_avg_performance)//2)
        if window < 3:
            return default_multiplier
            
        # Calculate moving average
        ma = np.convolve(daily_avg_performance, np.ones(window)/window, mode='valid')
        
        if len(ma) < 2:
            return default_multiplier
        
        # Get current performance (average of last 3 days) and MA
        current_perf = np.mean(daily_avg_performance[-3:])
        current_ma = ma[-1]
        
        # Calculate differences between performance and MA over time
        diffs = daily_avg_performance[-len(ma):] - ma
        
        # Calculate standard deviation of these differences
        std_diff = np.std(diffs)
        if std_diff == 0:
            std_diff = 0.1  # Avoid division by zero
        
        # Calculate current difference
        current_diff = current_perf - current_ma
        
        # Normalize the difference with bounds at -2std and 2std
        normalized_diff = max(min(current_diff / (2 * std_diff), 2), -2)
        
        # Apply sigmoid function to get a value between 0 and 1
        sigmoid = 1 / (1 + np.exp(-normalized_diff))
        
        # Scale to range [0.5, 3.0]
        multiplier = 0.5 + 2.5 * sigmoid
        
        print(f"Capital multiplier calculation:")
        print(f"Current performance: {current_perf:.2f}%")
        print(f"Moving average: {current_ma:.2f}%")
        print(f"Difference: {current_diff:.2f}%")
        print(f"Std of differences: {std_diff:.2f}")
        print(f"Normalized diff: {normalized_diff:.2f}")
        print(f"Final multiplier: {multiplier:.2f}x")
        
        return multiplier
        
    except Exception as e:
        print(f"Error calculating capital multiplier: {str(e)}")
        return default_multiplier

        
# Set capital multiplier (computed once at module import)
PER_SYMBOL_CAPITAL_MULTIPLIER = calculate_capital_multiplier(lookback_days_param/2)


initial_capital = 100000
symbols = list(TRADING_SYMBOLS.keys())
per_symbol_capital = initial_capital / len(symbols) * PER_SYMBOL_CAPITAL_MULTIPLIER  # Allow each symbol to potentially use full capital

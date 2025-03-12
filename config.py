import os
from typing import Dict, Any, List, Optional

# Trading symbols configuration
TRADING_SYMBOLS = {
    "SPY": {
        "yfinance": "SPY",
        "alpaca": "SPY",
        "description": "SPDR S&P 500 ETF Trust",
        "asset_class": "US Equity ETFs",
        "market_hours": {
            "timezone": "America/New_York",
            "start": "09:30",
            "end": "16:00",
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
    },
    "QQQ": {
        "yfinance": "QQQ",
        "alpaca": "QQQ",
        "description": "Invesco QQQ Trust (Nasdaq-100)",
        "asset_class": "US Equity ETFs",
        "market_hours": {
            "timezone": "America/New_York",
            "start": "09:30",
            "end": "16:00",
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
    },
    "IWM": {
        "yfinance": "IWM",
        "alpaca": "IWM",
        "description": "iShares Russell 2000 ETF",
        "asset_class": "US Equity ETFs",
        "market_hours": {
            "timezone": "America/New_York",
            "start": "09:30",
            "end": "16:00",
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
    },
    "GLD": {
        "yfinance": "GLD",
        "alpaca": "GLD",
        "description": "SPDR Gold Trust",
        "asset_class": "Commodities",
        "market_hours": {
            "timezone": "America/New_York",
            "start": "09:30",
            "end": "16:00",
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
    },
    "TLT": {
        "yfinance": "TLT",
        "alpaca": "TLT",
        "description": "iShares 20+ Year Treasury Bond ETF",
        "asset_class": "Bonds",
        "market_hours": {
            "timezone": "America/New_York",
            "start": "09:30",
            "end": "16:00",
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        }
    },
    "BTC": {
        "yfinance": "BTC-USD",
        "alpaca": "BTCUSD",
        "description": "Bitcoin",
        "asset_class": "Cryptocurrency",
        "market_hours": {
            "timezone": "UTC",
            "start": "00:00",
            "end": "23:59",
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        }
    },
    "ETH": {
        "yfinance": "ETH-USD",
        "alpaca": "ETHUSD",
        "description": "Ethereum",
        "asset_class": "Cryptocurrency",
        "market_hours": {
            "timezone": "UTC",
            "start": "00:00",
            "end": "23:59",
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        }
    }
}

# Trading costs by asset class
TRADING_COSTS = {
    "default": 0.0, 
    "US Equity ETFs": 0.0005,  # 0.05% per trade
    "Bonds": 0.0005,          # 0.05% per trade
    "Commodities": 0.001,     # 0.1% per trade
    "Cryptocurrency": 0.0025,  # 0.25% per trade
}

# Default risk percentage per trade
DEFAULT_RISK_PERCENT = 0.02  # 2% of portfolio value

# Time intervals for data and analysis
DEFAULT_INTERVAL = "5m"           # 5-minute interval for standard charts
DEFAULT_INTERVAL_WEEKLY = "1wk"   # Weekly interval for longer-term analysis
default_interval_yahoo = "5m"     # Yahoo Finance data retrieval interval
default_backtest_interval = 30    # Default number of days for backtesting

# Lookback periods
lookback_days_param = 5           # Default lookback period for parameters
lookback_days_weekly = 90         # Lookback period for weekly analysis

# Asset class allocations for different risk profiles
RISK_PROFILE_ALLOCATIONS = {
    "conservative": {
        "US Equity ETFs": 0.30,
        "Bonds": 0.50,
        "Commodities": 0.15,
        "Cryptocurrency": 0.05
    },
    "moderate": {
        "US Equity ETFs": 0.45,
        "Bonds": 0.30,
        "Commodities": 0.15,
        "Cryptocurrency": 0.10
    },
    "aggressive": {
        "US Equity ETFs": 0.60,
        "Bonds": 0.10,
        "Commodities": 0.15,
        "Cryptocurrency": 0.15
    }
}

# Strategy templates
STRATEGY_TEMPLATES = {
    "momentum": {
        "name": "Momentum Strategy",
        "description": "Follows trends using MACD, RSI, and stochastic indicators",
        "parameters": {
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "rsi_period": 14,
            "stochastic_k_period": 14,
            "stochastic_d_period": 3,
            "buy_up_lim": -2.0,
            "sell_down_lim": 2.0
        }
    },
    "mean_reversion": {
        "name": "Mean Reversion Strategy",
        "description": "Trades deviations from historical averages",
        "parameters": {
            "lookback_period": 20,
            "std_dev_trigger": 2.0,
            "max_holding_period": 5
        }
    },
    "adaptive": {
        "name": "Adaptive Strategy",
        "description": "Adjusts parameters based on market conditions",
        "parameters": {
            "volatility_lookback": 50,
            "regime_threshold": 0.5,
            "reactivity": 1.0
        }
    }
}

# API configuration defaults
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./portfolio_system.db")

# Optimization settings
OPTIMIZATION_WORKERS = int(os.getenv("OPTIMIZATION_WORKERS", "1"))

# Scheduler settings
SCHEDULER_TIMEZONE = "UTC"
SCHEDULER_ENABLED = True

# Asset groups (based on provided asset list)
ASSET_GROUPS = {
    "US Market Indices": ["SPY", "QQQ", "DIA", "IWM", "VTI", "RSP"],
    "US Equity Styles": ["VUG", "VTV", "SPLV", "SPHQ", "MOAT", "SPMO"],
    "US Sectors": ["XLF", "XLK", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU", "XLC"],
    "International": ["EFA", "VWO", "EMXC", "VGK", "EWJ", "BBJP"],
    "Fixed Income": ["TLT", "IEF", "SHY", "LQD", "HYG", "VCIT", "AGG", "BND"],
    "Commodities": ["GLD", "SLV", "PDBC", "USO", "UNG"],
    "Cryptocurrency": ["BTC", "ETH", "IBIT", "ETHA"]
}

# Get asset classes from the asset list
ASSET_CLASSES = list(set([config["asset_class"] for config in TRADING_SYMBOLS.values()]))

def get_default_params():
    """Get default strategy parameters"""
    return {
        'percent_increase_buy': 0.02,
        'percent_decrease_sell': 0.02,
        'sell_down_lim': 2.0,
        'sell_rolling_std': 20,
        'buy_up_lim': -2.0,
        'buy_rolling_std': 20,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'rsi_period': 14,
        'stochastic_k_period': 14,
        'stochastic_d_period': 3,
        'fractal_window': 100,
        'fractal_lags': [10, 20, 40],
        'reactivity': 1.0,
        'weights': {
            'weekly_macd_weight': 0.25,
            'weekly_rsi_weight': 0.25,
            'weekly_stoch_weight': 0.25,
            'weekly_complexity_weight': 0.25,
            'macd_weight': 0.4,
            'rsi_weight': 0.3,
            'stoch_weight': 0.2,
            'complexity_weight': 0.1
        }
    }

import json
import os
from datetime import datetime

def create_local_params(filename="best_params.json", include_sample=True):
    """Create a local parameters file with an initial structure"""
    # Create dictionary
    best_params_data = {}
    
    # Add sample parameter for SPY if requested
    if include_sample:
        current_date = datetime.now().strftime("%Y-%m-%d")
        best_params_data["SPY"] = {
            "best_params": {
                "percent_increase_buy": 0.02,
                "percent_decrease_sell": 0.02,
                "sell_down_lim": 2.0,
                "sell_rolling_std": 20,
                "buy_up_lim": -2.0,
                "buy_rolling_std": 20,
                "macd_fast": 12,
                "macd_slow": 26,
                "macd_signal": 9,
                "rsi_period": 14,
                "stochastic_k_period": 14,
                "stochastic_d_period": 3,
                "fractal_window": 100,
                "fractal_lags": [10, 20, 40],
                "reactivity": 1.0,
                "weights": {
                    "weekly_macd_weight": 0.25,
                    "weekly_rsi_weight": 0.25,
                    "weekly_stoch_weight": 0.25,
                    "weekly_complexity_weight": 0.25,
                    "macd_weight": 0.25,
                    "rsi_weight": 0.25,
                    "stoch_weight": 0.25,
                    "complexity_weight": 0.25
                }
            },
            "metrics": {
                "performance": 5.25,
                "win_rate": 58.33,
                "max_drawdown": -3.12
            },
            "performance_summary": {
                "max_performance": 8.75,
                "min_performance": 2.5,
                "avg_performance": 5.25
            },
            "date": current_date,
            "history": []
        }
        print(f"Added sample parameters for SPY")
    
    # Save to local file
    try:
        with open(filename, "w") as f:
            json.dump(best_params_data, f, indent=4)
        print(f"✅ Successfully created/updated local file '{filename}'")
    except Exception as e:
        print(f"Warning: Could not save to local file: {e}")
    
    return best_params_data

if __name__ == "__main__":
    params = create_local_params()
    print(f"Sample parameters file created with {len(params)} symbols")
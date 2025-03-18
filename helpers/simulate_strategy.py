import pandas as pd
import numpy as np
from indicators import calculate_macd, calculate_rsi, calculate_stochastic, generate_signals, get_default_params
from strategy import TradingStrategy
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import yfinance as yf
import pytz

def generate_sample_data(periods=2000):
    """Generate sample price data with a trend and some volatility"""
    # Create a more complex price pattern with multiple trends
    t = np.linspace(0, 20, periods)
    trend = 10 * np.sin(t/5) + t  # Adding sine wave to create cycles
    
    # Add more realistic volatility
    volatility = np.abs(np.sin(t/10)) + 0.5  # Dynamic volatility
    noise = np.random.normal(0, volatility, periods)
    
    # Combine trend and noise with more pronounced movements
    close = 100 + trend + noise.cumsum() * 0.3
    
    # Generate OHLC data with more realistic spreads
    data = pd.DataFrame({
        'open': close + np.random.normal(0, 0.8, periods),
        'high': close + np.abs(np.random.normal(1.5, 0.8, periods)),
        'low': close - np.abs(np.random.normal(1.5, 0.8, periods)),
        'close': close,
        'volume': np.random.randint(1000, 50000, periods) * (1 + np.abs(np.random.normal(0, 0.3, periods)))
    }, index=pd.date_range(
        start=datetime.now(pytz.UTC) - timedelta(days=30),
        periods=periods,
        freq='5min',
        tz='UTC'  # Explicitly set timezone to UTC
    ))
    
    return data

def analyze_single_point(data: pd.DataFrame, point_index: int):
    """Analyze a specific point in time, showing all calculations"""
    params = get_default_params()
    
    # Calculate individual indicators
    macd = calculate_macd(data)
    rsi = calculate_rsi(data)
    stoch = calculate_stochastic(data)
    
    # Get the signals
    signals, daily_data, weekly_data = generate_signals(data, params)
    
    # Get values at the specific point
    point = {
        'MACD': macd.iloc[point_index],
        'RSI': rsi.iloc[point_index],
        'Stochastic': stoch.iloc[point_index],
        'Daily Composite': daily_data['Composite'].iloc[point_index],
        'Daily Upper Limit': daily_data['Up_Lim'].iloc[point_index],
        'Daily Lower Limit': daily_data['Down_Lim'].iloc[point_index],
        'Weekly Composite': weekly_data['Composite'].iloc[point_index],
        'Weekly Upper Limit': weekly_data['Up_Lim'].iloc[point_index],
        'Weekly Lower Limit': weekly_data['Down_Lim'].iloc[point_index],
        'Signal': signals['signal'].iloc[point_index]
    }
    
    return point

def plot_analysis(data: pd.DataFrame, signals, daily_data, weekly_data):
    """Plot the analysis results with enhanced visualizations"""
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 15))
    
    # Plot 1: Price and Signals with volume
    ax1_volume = ax1.twinx()
    ax1.plot(data.index, data['close'], label='Price', color='blue', alpha=0.7)
    buy_signals = signals[signals['signal'] == 1].index
    sell_signals = signals[signals['signal'] == -1].index
    
    # Plot signals with price labels
    for idx in buy_signals:
        ax1.scatter(idx, data.loc[idx, 'close'], color='green', marker='^', s=100)
        ax1.text(idx, data.loc[idx, 'close'], f'\n${data.loc[idx, "close"]:.2f}', 
                ha='center', va='bottom', color='green')
    
    for idx in sell_signals:
        ax1.scatter(idx, data.loc[idx, 'close'], color='red', marker='v', s=100)
        ax1.text(idx, data.loc[idx, 'close'], f'\n${data.loc[idx, "close"]:.2f}', 
                ha='center', va='top', color='red')
    
    # Plot volume bars
    volume_data = data['volume'].rolling(window=5).mean()  # Smoothed volume
    ax1_volume.fill_between(data.index, volume_data, color='gray', alpha=0.3)
    ax1_volume.set_ylabel('Volume')
    ax1.set_ylabel('Price')
    
    ax1.set_title('Price Action with Trading Signals')
    ax1.legend(['Price', 'Buy Signal', 'Sell Signal'])
    
    # Plot 2: Daily Composite with signals
    ax2.plot(daily_data.index, daily_data['Composite'], label='Daily Composite', color='blue')
    ax2.plot(daily_data.index, daily_data['Up_Lim'], '--', label='Upper Limit', color='green', alpha=0.6)
    ax2.plot(daily_data.index, daily_data['Down_Lim'], '--', label='Lower Limit', color='red', alpha=0.6)
    ax2.fill_between(daily_data.index, daily_data['Up_Lim'], daily_data['Down_Lim'], 
                     color='gray', alpha=0.1)
    ax2.set_title('Daily Composite Indicator')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Weekly Composite with signals
    ax3.plot(weekly_data.index, weekly_data['Composite'], label='Weekly Composite', color='purple')
    ax3.plot(weekly_data.index, weekly_data['Up_Lim'], '--', label='Upper Limit', color='green', alpha=0.6)
    ax3.plot(weekly_data.index, weekly_data['Down_Lim'], '--', label='Lower Limit', color='red', alpha=0.6)
    ax3.fill_between(weekly_data.index, weekly_data['Up_Lim'], weekly_data['Down_Lim'], 
                     color='gray', alpha=0.1)
    ax3.set_title('Weekly Composite Indicator (35-min bars)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('strategy_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def simulate_and_plot(symbol='SPY', start_date=None, end_date=None):
    # If dates not provided, use last 5 trading days
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=5)
    
    # Fetch data
    print(f"Fetching {symbol} data from {start_date} to {end_date}")
    data = yf.download(symbol, start=start_date, end=end_date, interval=config.DEFAULT_INTERVAL)
    
    if len(data) == 0:
        print("No data fetched. Please check your dates and symbol.")
        return
    
    # Convert column names to lowercase for consistency
    data.columns = data.columns.str.lower()
    
    # Generate signals
    params = get_default_params()
    signals, daily_data, weekly_data = generate_signals(data, params)
    
    # Create the plot
    plt.figure(figsize=(15, 12))
    
    # Plot 1: Price and Signals
    plt.subplot(3, 1, 1)
    plt.plot(data.index, data['close'], label='Price', color='blue', alpha=0.6)
    
    # Plot buy signals
    buy_signals = signals[signals['signal'] == 1]
    if len(buy_signals) > 0:
        plt.scatter(buy_signals.index, data.loc[buy_signals.index, 'close'], 
                   marker='^', color='green', s=100, label='Buy Signal')
    
    # Plot sell signals
    sell_signals = signals[signals['signal'] == -1]
    if len(sell_signals) > 0:
        plt.scatter(sell_signals.index, data.loc[sell_signals.index, 'close'], 
                   marker='v', color='red', s=100, label='Sell Signal')
    
    plt.title(f'{symbol} Price and Signals')
    plt.legend()
    plt.grid(True)
    
    # Plot 2: Daily Composite
    plt.subplot(3, 1, 2)
    plt.plot(signals.index, signals['daily_composite'], label='Daily Composite', color='blue')
    plt.plot(signals.index, signals['daily_up_lim'], '--', label='Upper Limit', color='green')
    plt.plot(signals.index, signals['daily_down_lim'], '--', label='Lower Limit', color='red')
    plt.fill_between(signals.index, signals['daily_up_lim'], signals['daily_down_lim'], 
                     color='gray', alpha=0.1)
    plt.title('Daily Composite Indicator')
    plt.legend()
    plt.grid(True)
    
    # Plot 3: Weekly Composite
    plt.subplot(3, 1, 3)
    plt.plot(signals.index, signals['weekly_composite'], label='Weekly Composite', color='purple')
    plt.plot(signals.index, signals['weekly_up_lim'], '--', label='Upper Limit', color='green')
    plt.plot(signals.index, signals['weekly_down_lim'], '--', label='Lower Limit', color='red')
    plt.fill_between(signals.index, signals['weekly_up_lim'], signals['weekly_down_lim'], 
                     color='gray', alpha=0.1)
    plt.title('Weekly Composite Indicator (35-min bars)')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    
    # Save the plot
    plt.savefig('strategy_simulation.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Print statistics
    print("\nStrategy Statistics:")
    print(f"Number of buy signals: {len(buy_signals)}")
    print(f"Number of sell signals: {len(sell_signals)}")
    print(f"\nDaily Composite Stats:")
    print(f"Mean: {signals['daily_composite'].mean():.4f}")
    print(f"Std: {signals['daily_composite'].std():.4f}")
    print(f"Range: {signals['daily_composite'].min():.4f} to {signals['daily_composite'].max():.4f}")
    print(f"\nWeekly Composite Stats:")
    print(f"Mean: {signals['weekly_composite'].mean():.4f}")
    print(f"Std: {signals['weekly_composite'].std():.4f}")
    print(f"Range: {signals['weekly_composite'].min():.4f} to {signals['weekly_composite'].max():.4f}")

def main():
    # Generate sample data with more periods
    data = generate_sample_data(2000)  # Using 2000 periods
    
    # Initialize strategy
    strategy = TradingStrategy("SPY")
    params = get_default_params()
    
    # Generate signals
    signals, daily_data, weekly_data = generate_signals(data, params)
    
    # Analyze multiple signal points
    signal_points = signals[signals['signal'] != 0].index
    if len(signal_points) > 0:
        # Analyze first buy and first sell signal
        buy_points = signals[signals['signal'] == 1].index
        sell_points = signals[signals['signal'] == -1].index
        
        points_to_analyze = []
        if len(buy_points) > 0:
            points_to_analyze.append(('BUY', data.index.get_loc(buy_points[0])))
        if len(sell_points) > 0:
            points_to_analyze.append(('SELL', data.index.get_loc(sell_points[0])))
        
        for signal_type, point_index in points_to_analyze:
            analysis = analyze_single_point(data, point_index)
            
            print(f"\n=== Sample {signal_type} Signal Analysis ===")
            print(f"Timestamp: {data.index[point_index]}")
            print("\nRaw Indicators:")
            print(f"MACD: {analysis['MACD']:.4f}")
            print(f"RSI: {analysis['RSI']:.4f}")
            print(f"Stochastic: {analysis['Stochastic']:.4f}")
            
            print("\nComposite Indicators:")
            print(f"Daily Composite: {analysis['Daily Composite']:.4f}")
            print(f"Daily Upper Limit: {analysis['Daily Upper Limit']:.4f}")
            print(f"Daily Lower Limit: {analysis['Daily Lower Limit']:.4f}")
            
            print(f"\nWeekly Composite: {analysis['Weekly Composite']:.4f}")
            print(f"Weekly Upper Limit: {analysis['Weekly Upper Limit']:.4f}")
            print(f"Weekly Lower Limit: {analysis['Weekly Lower Limit']:.4f}")
            
            print(f"\nFinal Signal: {analysis['Signal']}")
        
        # Count signals
        buy_signals = (signals['signal'] == 1).sum()
        sell_signals = (signals['signal'] == -1).sum()
        print(f"\nTotal Signals in Sample:")
        print(f"Buy Signals: {buy_signals}")
        print(f"Sell Signals: {sell_signals}")
        
        # Calculate performance metrics
        signal_changes = data.loc[signal_points, 'close'].pct_change()
        print(f"\nSignal Performance Metrics:")
        print(f"Average Signal Price Change: {signal_changes.mean():.2%}")
        print(f"Signal Price Change Std Dev: {signal_changes.std():.2%}")
        
        # Calculate win rate
        profitable_signals = (signal_changes > 0).sum()
        total_signals = len(signal_changes)
        if total_signals > 0:
            win_rate = profitable_signals / total_signals
            print(f"Win Rate: {win_rate:.2%}")
    
    # Create visualization
    plot_analysis(data, signals, daily_data, weekly_data)
    print("\nVisualization saved as 'strategy_analysis.png'")
    
    # Run simulation
    simulate_and_plot()

if __name__ == "__main__":
    # Use the last 5 trading days by default
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    simulate_and_plot(start_date=start_date, end_date=end_date)

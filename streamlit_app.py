import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd
from alpaca.trading.client import TradingClient
from datetime import datetime
import pytz
from config import TRADING_SYMBOLS
from trading import TradingExecutor
from strategy import TradingStrategy
from backtest_individual import run_backtest
import json
import logging
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('streamlit.log'),  # Separate log file for Streamlit
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TradingManager:
    def __init__(self):
        self.trading_client = None
        self.strategies = {}
        self.trading_executors = {}
        self.symbols = []
        self.is_running = False
        self.trading_thread = None
        self.last_check = {}
        
    def initialize(self):
        """Initialize trading components"""
        try:
            self.trading_client = TradingClient(
                os.getenv('ALPACA_API_KEY_paper'),
                os.getenv('ALPACA_SECRET_KEY_paper')
            )
            
            self.symbols = list(TRADING_SYMBOLS.keys())
            self.strategies = {symbol: TradingStrategy(symbol) for symbol in self.symbols}
            self.trading_executors = {symbol: TradingExecutor(self.trading_client, symbol) for symbol in self.symbols}
            
            logger.info("Successfully initialized trading components")
            return True
        except Exception as e:
            logger.error(f"Error initializing trading components: {e}")
            return False
    
    def start_trading(self):
        """Start the trading loop in a separate thread"""
        if not self.is_running:
            self.is_running = True
            self.trading_thread = threading.Thread(target=self._trading_loop)
            self.trading_thread.daemon = True
            self.trading_thread.start()
            logger.info("Trading loop started")
    
    def stop_trading(self):
        """Stop the trading loop"""
        self.is_running = False
        if self.trading_thread:
            self.trading_thread.join()
            logger.info("Trading loop stopped")
    
    def _trading_loop(self):
        """Main trading loop"""
        while self.is_running:
            try:
                current_time = datetime.now(pytz.UTC)
                
                for symbol in self.symbols:
                    try:
                        # Check if 5 minutes have passed since last check
                        if (symbol in self.last_check and 
                            (current_time - self.last_check[symbol]).total_seconds() < 300):
                            continue
                            
                        # Generate signals
                        analysis = self.strategies[symbol].analyze()
                        if analysis and analysis['signal'] != 0:
                            signal_type = "LONG" if analysis['signal'] == 1 else "SHORT"
                            logger.info(f"Trading Signal for {symbol}: {signal_type}")
                            
                            # Execute trade
                            action = "BUY" if analysis['signal'] == 1 else "SELL"
                            self.trading_executors[symbol].execute_trade(
                                action=action,
                                analysis=analysis,
                                notify_callback=logger.info
                            )
                            
                        self.last_check[symbol] = current_time
                        
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                        continue
                
                # Sleep for 1 minute
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                time.sleep(60)

def initialize_trading_components():
    """Initialize trading components and store them in session state"""
    if 'trading_manager' not in st.session_state:
        trading_manager = TradingManager()
        if trading_manager.initialize():
            st.session_state.trading_manager = trading_manager
            return True
    return 'trading_manager' in st.session_state

# Streamlit app layout
st.set_page_config(page_title="Trading Bot Dashboard", layout="wide")

# Initialize trading components
initialize_trading_components()

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page",
    ["Dashboard", "Status", "Positions", "Account", "Indicators", "Signals", 
     "Plot", "Backtest", "Portfolio", "Trading", "Market Info", "Settings"]
)

# Trading control in sidebar
if 'trading_manager' in st.session_state:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Trading Control")
    
    if st.session_state.trading_manager.is_running:
        if st.sidebar.button("Stop Trading"):
            st.session_state.trading_manager.stop_trading()
            st.sidebar.success("Trading stopped")
    else:
        if st.sidebar.button("Start Trading"):
            st.session_state.trading_manager.start_trading()
            st.sidebar.success("Trading started")

# Dashboard page with real-time monitoring
def show_dashboard():
    if not st.session_state.get('trading_manager'):
        st.error("Trading components not initialized. Please check your API keys and try again.")
        return

    st.title("Trading Bot Dashboard")
    
    # Market Status
    market_open = is_market_hours()
    status_color = "" if market_open else ""
    st.markdown(f"### Market Status: {status_color} {'OPEN' if market_open else 'CLOSED'}")
    
    # Create three columns for the layout
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.subheader("Trading Status")
        status_container = st.empty()
        
        # Display current trading status for each symbol
        try:
            status_data = []
            for symbol in st.session_state.trading_manager.symbols:
                try:
                    analysis = st.session_state.trading_manager.strategies[symbol].analyze()
                    position = st.session_state.trading_manager.trading_executors[symbol].get_position()
                    position_str = "NEUTRAL"
                    if position:
                        qty = float(position.qty)
                        position_str = f"LONG ({qty})" if qty > 0 else f"SHORT ({abs(qty)})"
                    
                    status_data.append({
                        "Symbol": symbol,
                        "Position": position_str,
                        "Current Price": f"${analysis['current_price']:.2f}" if analysis else "N/A",
                        "Daily Score": f"{analysis['daily_composite']:.4f}" if analysis else "N/A",
                        "Weekly Score": f"{analysis['weekly_composite']:.4f}" if analysis else "N/A"
                    })
                except Exception as e:
                    logger.error(f"Error getting status for {symbol}: {e}")
                    status_data.append({
                        "Symbol": symbol,
                        "Position": "Error",
                        "Current Price": "Error",
                        "Daily Score": "Error",
                        "Weekly Score": "Error"
                    })
            
            status_df = pd.DataFrame(status_data)
            status_container.dataframe(status_df, use_container_width=True)
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            status_container.error("Failed to load trading status")
        
    with col2:
        # Trading Parameters
        st.subheader("Trading Parameters")
        params_container = st.empty()
        
        try:
            params_data = []
            try:
                with open("best_params.json", "r") as f:
                    best_params_data = json.load(f)
                    for symbol in st.session_state.trading_manager.symbols:
                        if symbol in best_params_data:
                            params = best_params_data[symbol]['best_params']
                            last_update = best_params_data[symbol].get('date', 'N/A')
                            params_data.append({
                                "Symbol": symbol,
                                "Parameters": str(params),
                                "Last Updated": last_update
                            })
            except FileNotFoundError:
                for symbol in st.session_state.trading_manager.symbols:
                    params_data.append({
                        "Symbol": symbol,
                        "Parameters": "Using defaults",
                        "Last Updated": "N/A"
                    })
            
            params_df = pd.DataFrame(params_data)
            params_container.dataframe(params_df, use_container_width=True)
        except Exception as e:
            logger.error(f"Error loading parameters: {e}")
            params_container.error("Failed to load parameters")
    
    with col3:
        # Latest Signals
        st.subheader("Latest Signals")
        signals_container = st.empty()
        
        try:
            signals_data = []
            for symbol in st.session_state.trading_manager.symbols:
                try:
                    analysis = st.session_state.trading_manager.strategies[symbol].analyze()
                    if analysis and analysis['signal'] != 0:
                        signal_type = "LONG" if analysis['signal'] == 1 else "SHORT"
                        signals_data.append({
                            "Symbol": symbol,
                            "Signal": signal_type,
                            "Price": f"${analysis['current_price']:.2f}",
                            "Time": analysis['bar_time']
                        })
                except Exception as e:
                    logger.error(f"Error getting signals for {symbol}: {e}")
                    continue
            
            if signals_data:
                signals_df = pd.DataFrame(signals_data)
                signals_container.dataframe(signals_df, use_container_width=True)
            else:
                signals_container.write("No active signals")
        except Exception as e:
            logger.error(f"Error updating signals: {e}")
            signals_container.error("Failed to load signals")
    
    # Create a section for logs
    st.subheader("Trading Log")
    log_container = st.empty()
    
    try:
        with open('streamlit.log', 'r') as f:
            logs = f.readlines()
            # Show last 20 log lines
            log_text = ''.join(logs[-20:])
            log_container.text_area("", value=log_text, height=300)
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        log_container.text_area("", value=f"Error reading logs: {e}", height=300)
    
    # Auto-refresh using JavaScript
    st.markdown("""
        <script>
            function refreshPage() {
                location.reload();
            }
            setInterval(refreshPage, 5000);
        </script>
    """, unsafe_allow_html=True)

# Status page
def show_status():
    if not st.session_state.get('trading_manager'):
        st.error("Trading components not initialized. Please check your API keys and try again.")
        return

    st.title("Trading Status")
    symbol = st.selectbox("Select a symbol", ["All"] + st.session_state.trading_manager.symbols)
    if symbol == "All":
        symbols_to_check = st.session_state.trading_manager.symbols
    else:
        symbols_to_check = [symbol]
    
    for sym in symbols_to_check:
        try:
            analysis = st.session_state.trading_manager.strategies[sym].analyze()
            if not analysis:
                st.write(f"No data available for {sym}")
                continue
            position = "LONG" if st.session_state.trading_manager.strategies[sym].current_position == 1 else "SHORT" if st.session_state.trading_manager.strategies[sym].current_position == -1 else "NEUTRAL"
            st.write(f"**{sym} Status:**")
            st.write(f"Position: {position}")
            st.write(f"Current Price: ${analysis['current_price']:.2f}")
            st.write(f"Daily Composite: {analysis['daily_composite']:.4f}")
            st.write(f"Weekly Composite: {analysis['weekly_composite']:.4f}")
        except Exception as e:
            st.error(f"Error analyzing {sym}: {e}")

# Positions page
def show_positions():
    if not st.session_state.get('trading_manager'):
        st.error("Trading components not initialized. Please check your API keys and try again.")
        return

    st.title("Positions Details")
    try:
        positions = st.session_state.trading_manager.trading_client.get_all_positions()
        if positions:
            df = pd.DataFrame([
                {
                    "Symbol": p.symbol,
                    "Quantity": p.qty,
                    "Entry Price": float(p.avg_entry_price),
                    "Current Price": float(p.current_price),
                    "Market Value": float(p.market_value),
                    "Unrealized P&L": float(p.unrealized_pl),
                    "Unrealized P&L (%)": float(p.unrealized_plpc) * 100
                } for p in positions
            ])
            st.dataframe(df)
        else:
            st.write("No open positions")
    except Exception as e:
        st.error(f"Error getting positions: {e}")

# Account page
def show_account():
    if not st.session_state.get('trading_manager'):
        st.error("Trading components not initialized. Please check your API keys and try again.")
        return

    st.title("Account Balance")
    try:
        account = st.session_state.trading_manager.trading_client.get_account()
        st.write(f"Cash: ${float(account.cash):.2f}")
        st.write(f"Portfolio Value: ${float(account.portfolio_value):.2f}")
        st.write(f"Buying Power: ${float(account.buying_power):.2f}")
        st.write(f"Today's P&L: ${float(account.equity) - float(account.last_equity):.2f}")
    except Exception as e:
        st.error(f"Error getting account info: {e}")

# Indicators page
def show_indicators():
    if not st.session_state.get('trading_manager'):
        st.error("Trading components not initialized. Please check your API keys and try again.")
        return

    st.title("Indicator Values")
    symbol = st.selectbox("Select a symbol", ["All"] + st.session_state.trading_manager.symbols)
    if symbol == "All":
        symbols_to_check = st.session_state.trading_manager.symbols
    else:
        symbols_to_check = [symbol]
    
    for sym in symbols_to_check:
        try:
            analysis = st.session_state.trading_manager.strategies[sym].analyze()
            if not analysis:
                st.write(f"No data available for {sym}")
                continue
            st.write(f"**{sym} Indicators:**")
            st.write(f"Daily Composite: {analysis['daily_composite']:.4f}")
            st.write(f"Weekly Composite: {analysis['weekly_composite']:.4f}")
            st.write(f"Price Change (5min): {analysis['price_change_5m'] * 100:.2f}%")
            st.write(f"Price Change (1hr): {analysis['price_change_1h'] * 100:.2f}%")
        except Exception as e:
            st.error(f"Error analyzing {sym}: {e}")

# Signals page
def show_signals():
    if not st.session_state.get('trading_manager'):
        st.error("Trading components not initialized. Please check your API keys and try again.")
        return

    st.title("Trading Signals")
    symbol = st.selectbox("Select a symbol", ["All"] + st.session_state.trading_manager.symbols)
    if symbol == "All":
        symbols_to_check = st.session_state.trading_manager.symbols
    else:
        symbols_to_check = [symbol]
    
    for sym in symbols_to_check:
        try:
            analysis = st.session_state.trading_manager.strategies[sym].analyze()
            if not analysis:
                st.write(f"No data available for {sym}")
                continue
            st.write(f"**{sym} Signals:**")
            st.write(f"Daily Composite: {analysis['daily_composite']:.4f}")
        except Exception as e:
            st.error(f"Error analyzing {sym}: {e}")

# Plot page
def show_plot():
    if not st.session_state.get('trading_manager'):
        st.error("Trading components not initialized. Please check your API keys and try again.")
        return

    st.title("Strategy Visualization")
    symbol = st.selectbox("Select a symbol", st.session_state.trading_manager.symbols)
    days = st.number_input("Enter number of days", min_value=1, max_value=30, value=5)
    if st.button("Generate Plot"):
        try:
            buf, stats = create_strategy_plot(symbol, days)
            st.image(buf, caption=f"{symbol} Strategy Plot ({days} days)")
            st.write(f"Trading Days: {stats['trading_days']}")
            st.write(f"Price Change: {stats['price_change']:.2f}%")
            st.write(f"Buy Signals: {stats['buy_signals']}")
            st.write(f"Sell Signals: {stats['sell_signals']}")
        except Exception as e:
            st.error(f"Error generating plot: {e}")

# Backtest page
def show_backtest():
    if not st.session_state.get('trading_manager'):
        st.error("Trading components not initialized. Please check your API keys and try again.")
        return

    st.title("Backtest Simulation")
    symbol = st.selectbox("Select a symbol", ["Portfolio"] + st.session_state.trading_manager.symbols)
    days = st.number_input("Enter number of days", min_value=1, max_value=30, value=5)
    if st.button("Run Backtest"):
        try:
            if symbol == "Portfolio":
                result = run_portfolio_backtest(st.session_state.trading_manager.symbols, days)
                st.write(f"Initial Capital: ${result['metrics']['initial_capital']:,.2f}")
                st.write(f"Final Value: ${result['metrics']['final_value']:,.2f}")
                st.write(f"Total Return: {result['metrics']['total_return']:.2f}%")
                st.write(f"Max Drawdown: {result['metrics']['max_drawdown']:.2f}%")
                plot_buffer = create_portfolio_backtest_plot(result)
                st.image(plot_buffer, caption="Portfolio Backtest")
            else:
                result = run_backtest(symbol, days)
                st.write(f"Initial Capital: ${result['metrics']['initial_capital']:,.2f}")
                st.write(f"Final Value: ${result['metrics']['final_value']:,.2f}")
                st.write(f"Total Return: {result['metrics']['total_return']:.2f}%")
                st.write(f"Max Drawdown: {result['metrics']['max_drawdown']:.2f}%")
                plot_buffer = create_backtest_plot(result)
                st.image(plot_buffer, caption=f"{symbol} Backtest")
        except Exception as e:
            st.error(f"Error running backtest: {e}")

# Portfolio page
def show_portfolio():
    if not st.session_state.get('trading_manager'):
        st.error("Trading components not initialized. Please check your API keys and try again.")
        return

    st.title("Portfolio History")
    timeframe = st.selectbox("Select a timeframe", ["1D", "1H", "15Min"])
    period = st.selectbox("Select a period", ["1M", "1W", "1D"])
    if st.button("Show Portfolio History"):
        try:
            portfolio_history = get_portfolio_history(timeframe=timeframe, period=period)
            plot_buffer = create_portfolio_plot(portfolio_history)
            st.image(plot_buffer, caption=f"Portfolio History (Timeframe: {timeframe}, Period: {period})")
        except Exception as e:
            st.error(f"Error getting portfolio history: {e}")

# Trading page
def show_trading():
    if not st.session_state.get('trading_manager'):
        st.error("Trading components not initialized. Please check your API keys and try again.")
        return

    st.title("Trading")
    symbol = st.selectbox("Select a symbol", st.session_state.trading_manager.symbols)
    action = st.selectbox("Select an action", ["Open", "Close"])
    amount = st.number_input("Enter amount", value=1000)
    if st.button("Execute Trade"):
        try:
            if action == "Open":
                # Get current price from strategy
                analysis = st.session_state.trading_manager.strategies[symbol].analyze()
                if not analysis:
                    st.error(f"Unable to get current price for {symbol}")
                    return
                current_price = analysis['current_price']
                # Execute the trade using the appropriate executor
                st.session_state.trading_manager.trading_executors[symbol].open_position(amount, current_price, logger.info)
                st.success(f"Successfully opened {symbol} position with amount ${amount}")
            elif action == "Close":
                st.session_state.trading_manager.trading_executors[symbol].close_position(logger.info)
                st.success(f"Successfully closed {symbol} position")
        except Exception as e:
            st.error(f"Error executing trade: {e}")

# Market Info page
def show_market_info():
    if not st.session_state.get('trading_manager'):
        st.error("Trading components not initialized. Please check your API keys and try again.")
        return

    st.title("Market Information")
    for symbol in st.session_state.trading_manager.symbols:
        config = TRADING_SYMBOLS[symbol]
        st.write(f"**{symbol} ({config['name']}):**")
        st.write(f"Market: {config['market']}")
        st.write(f"Interval: {config['interval']}")
        st.write(f"Trading Hours: {config['market_hours']['start']} - {config['market_hours']['end']} ({config['market_hours']['timezone']})")

# Settings page
def show_settings():
    if not st.session_state.get('trading_manager'):
        st.error("Trading components not initialized. Please check your API keys and try again.")
        return

    st.title("Settings")
    st.write("No settings available yet")

def is_market_hours():
    """Check if it's currently market hours (9:30 AM - 4:00 PM Eastern, Monday-Friday)"""
    et_tz = pytz.timezone('US/Eastern')
    now = datetime.now(et_tz)
    
    # Check if it's a weekday
    if now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return False
    
    # Market hours are 9:30 AM - 4:00 PM Eastern
    market_start = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_end = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_start <= now <= market_end

# Main execution
if __name__ == "__main__":
    # Display the selected page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Status":
        show_status()
    elif page == "Positions":
        show_positions()
    elif page == "Account":
        show_account()
    elif page == "Indicators":
        show_indicators()
    elif page == "Signals":
        show_signals()
    elif page == "Plot":
        show_plot()
    elif page == "Backtest":
        show_backtest()
    elif page == "Portfolio":
        show_portfolio()
    elif page == "Trading":
        show_trading()
    elif page == "Market Info":
        show_market_info()
    elif page == "Settings":
        show_settings()
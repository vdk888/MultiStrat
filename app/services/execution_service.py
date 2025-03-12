import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.database.repository.portfolios import PortfolioRepository
from app.database.repository.assets import AssetRepository
from app.core.config import get_settings

# Set up logger
logger = logging.getLogger(__name__)

class ExecutionService:
    """
    Service for trade execution via Alpaca API
    """
    
    def __init__(self):
        """Initialize the execution service"""
        self.settings = get_settings()
        
        # Initialize Alpaca client
        self.alpaca_client = None
        self.is_initialized = False
        
        # Try to initialize Alpaca client if API keys are available
        self._initialize_alpaca()
    
    def _initialize_alpaca(self) -> bool:
        """Initialize Alpaca API client"""
        # Check if API keys are available
        api_key = os.getenv("ALPACA_API_KEY")
        api_secret = os.getenv("ALPACA_SECRET_KEY")
        base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
        if not api_key or not api_secret:
            logger.warning("Alpaca API keys not found. Trade execution will be simulated.")
            return False
        
        try:
            # Use delayed import to avoid startup dependency issues
            from alpaca.trading.client import TradingClient
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce
            
            # Store client and enums for later use
            self.TradingClient = TradingClient
            self.MarketOrderRequest = MarketOrderRequest
            self.OrderSide = OrderSide
            self.TimeInForce = TimeInForce
            
            # Initialize client
            self.alpaca_client = TradingClient(api_key, api_secret, paper=True)
            
            # Test connection
            account = self.alpaca_client.get_account()
            logger.info(f"Alpaca API connected. Account ID: {account.id}, Status: {account.status}")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Alpaca client: {str(e)}")
            return False
    
    def execute_trade(self, db: Session, trade_id: int) -> Any:
        """
        Execute a trade via Alpaca API
        
        Args:
            db: Database session
            trade_id: Trade ID to execute
            
        Returns:
            Updated trade record
        """
        try:
            # Get trade from database
            trade = db.query("Trade").filter("Trade.id" == trade_id).first()
            if not trade:
                raise ValueError(f"Trade with ID {trade_id} not found")
            
            # Get asset
            asset = AssetRepository.get_asset(db, asset_id=trade.asset_id)
            if not asset:
                raise ValueError(f"Asset with ID {trade.asset_id} not found")
            
            # Determine symbol to use with Alpaca
            symbol = asset.alpaca_symbol or asset.symbol
            
            # Check if Alpaca client is initialized
            if not self.is_initialized and not self._initialize_alpaca():
                # Simulate trade execution
                logger.info(f"Simulating trade execution for {symbol} ({trade.side}, {trade.quantity} shares)")
                
                # Update trade in database
                trade.status = "filled"
                trade.broker_order_id = f"sim-{datetime.utcnow().timestamp()}"
                db.commit()
                
                # Update portfolio asset
                portfolio_asset = PortfolioRepository.get_portfolio_asset(db, trade.portfolio_id, trade.asset_id)
                if portfolio_asset:
                    new_quantity = portfolio_asset.quantity
                    if trade.side.lower() == "buy":
                        new_quantity += trade.quantity
                    elif trade.side.lower() == "sell":
                        new_quantity = max(0, new_quantity - trade.quantity)
                    
                    PortfolioRepository.update_portfolio_asset(
                        db, 
                        trade.portfolio_id, 
                        trade.asset_id, 
                        {"quantity": new_quantity}
                    )
                
                return trade
            
            # Execute trade via Alpaca API
            side = self.OrderSide.BUY if trade.side.lower() == "buy" else self.OrderSide.SELL
            
            # Create order request
            order_request = self.MarketOrderRequest(
                symbol=symbol,
                qty=trade.quantity,
                side=side,
                time_in_force=self.TimeInForce.DAY
            )
            
            # Submit order
            order = self.alpaca_client.submit_order(order_request)
            
            # Update trade in database
            trade.status = "submitted"
            trade.broker_order_id = order.id
            db.commit()
            
            # In a real implementation, we would listen for order updates
            # and update the trade status accordingly. For simplicity,
            # we'll just mark it as filled immediately.
            trade.status = "filled"
            db.commit()
            
            # Update portfolio asset
            portfolio_asset = PortfolioRepository.get_portfolio_asset(db, trade.portfolio_id, trade.asset_id)
            if portfolio_asset:
                new_quantity = portfolio_asset.quantity
                if trade.side.lower() == "buy":
                    new_quantity += trade.quantity
                elif trade.side.lower() == "sell":
                    new_quantity = max(0, new_quantity - trade.quantity)
                
                PortfolioRepository.update_portfolio_asset(
                    db, 
                    trade.portfolio_id, 
                    trade.asset_id, 
                    {"quantity": new_quantity}
                )
            
            return trade
            
        except Exception as e:
            logger.error(f"Error executing trade {trade_id}: {str(e)}")
            
            # Update trade status to failed
            try:
                trade.status = "failed"
                trade.notes = str(e)
                db.commit()
            except:
                pass
            
            raise
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get Alpaca account information
        
        Returns:
            Account information
        """
        if not self.is_initialized and not self._initialize_alpaca():
            return {
                "status": "unavailable",
                "message": "Alpaca API not initialized",
                "buying_power": 0,
                "cash": 0,
                "portfolio_value": 0
            }
        
        try:
            account = self.alpaca_client.get_account()
            
            return {
                "id": account.id,
                "status": account.status,
                "buying_power": float(account.buying_power),
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "equity": float(account.equity),
                "currency": account.currency,
                "pattern_day_trader": account.pattern_day_trader,
                "trading_blocked": account.trading_blocked,
                "transfers_blocked": account.transfers_blocked,
                "account_blocked": account.account_blocked,
                "created_at": account.created_at.isoformat() if account.created_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting account information: {str(e)}")
            
            return {
                "status": "error",
                "message": str(e),
                "buying_power": 0,
                "cash": 0,
                "portfolio_value": 0
            }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions from Alpaca
        
        Returns:
            List of positions
        """
        if not self.is_initialized and not self._initialize_alpaca():
            return []
        
        try:
            positions = self.alpaca_client.get_all_positions()
            
            result = []
            for position in positions:
                result.append({
                    "symbol": position.symbol,
                    "quantity": float(position.qty),
                    "market_value": float(position.market_value),
                    "cost_basis": float(position.cost_basis),
                    "avg_entry_price": float(position.avg_entry_price),
                    "unrealized_pl": float(position.unrealized_pl),
                    "unrealized_plpc": float(position.unrealized_plpc),
                    "current_price": float(position.current_price),
                    "side": position.side
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []
    
    def get_orders(self, status: str = "open") -> List[Dict[str, Any]]:
        """
        Get orders from Alpaca
        
        Args:
            status: Order status filter (open, closed, all)
            
        Returns:
            List of orders
        """
        if not self.is_initialized and not self._initialize_alpaca():
            return []
        
        try:
            if status == "open":
                orders = self.alpaca_client.get_orders()
            elif status == "closed":
                orders = self.alpaca_client.get_orders(status="closed", limit=50)
            else:
                # Get both open and closed orders
                open_orders = self.alpaca_client.get_orders()
                closed_orders = self.alpaca_client.get_orders(status="closed", limit=50)
                orders = open_orders + closed_orders
            
            result = []
            for order in orders:
                result.append({
                    "id": order.id,
                    "symbol": order.symbol,
                    "quantity": float(order.qty),
                    "side": order.side,
                    "type": order.type,
                    "time_in_force": order.time_in_force,
                    "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
                    "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                    "status": order.status,
                    "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                    "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                    "limit_price": float(order.limit_price) if order.limit_price else None,
                    "stop_price": float(order.stop_price) if order.stop_price else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            return []
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order in Alpaca
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Result of cancel operation
        """
        if not self.is_initialized and not self._initialize_alpaca():
            return {
                "success": False,
                "message": "Alpaca API not initialized"
            }
        
        try:
            self.alpaca_client.cancel_order(order_id)
            
            return {
                "success": True,
                "order_id": order_id,
                "message": "Order canceled successfully"
            }
            
        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {str(e)}")
            
            return {
                "success": False,
                "order_id": order_id,
                "message": str(e)
            }

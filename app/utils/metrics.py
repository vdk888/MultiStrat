import numpy as np
from typing import List, Union, Optional
import logging

# Set up logger
logger = logging.getLogger(__name__)

def calculate_sharpe_ratio(returns: Union[List[float], np.ndarray], 
                          risk_free_rate: float = 0.0, 
                          periods_per_year: int = 252) -> float:
    """
    Calculate the Sharpe ratio
    
    Args:
        returns: List or array of returns
        risk_free_rate: Annual risk-free rate (default: 0.0)
        periods_per_year: Number of periods in a year (default: 252 for daily returns)
        
    Returns:
        Sharpe ratio
    """
    try:
        if not isinstance(returns, np.ndarray):
            returns = np.array(returns)
        
        if len(returns) < 2:
            return 0.0
        
        # Convert annual risk-free rate to per-period rate
        rf_per_period = (1 + risk_free_rate) ** (1 / periods_per_year) - 1
        
        # Calculate excess returns
        excess_returns = returns - rf_per_period
        
        # Calculate mean and standard deviation of excess returns
        mean_excess_return = np.mean(excess_returns)
        std_excess_return = np.std(excess_returns, ddof=1)  # Use sample standard deviation
        
        if std_excess_return == 0:
            return 0.0
        
        # Calculate Sharpe ratio and annualize
        sharpe_ratio = mean_excess_return / std_excess_return
        annualized_sharpe = sharpe_ratio * np.sqrt(periods_per_year)
        
        return float(annualized_sharpe)
    
    except Exception as e:
        logger.error(f"Error calculating Sharpe ratio: {str(e)}")
        return 0.0

def calculate_max_drawdown(values: Union[List[float], np.ndarray]) -> float:
    """
    Calculate the maximum drawdown
    
    Args:
        values: List or array of portfolio values
        
    Returns:
        Maximum drawdown as a percentage
    """
    try:
        if not isinstance(values, np.ndarray):
            values = np.array(values)
        
        if len(values) < 2:
            return 0.0
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(values)
        
        # Calculate drawdowns
        drawdowns = (running_max - values) / running_max
        
        # Get maximum drawdown
        max_drawdown = np.max(drawdowns)
        
        return float(max_drawdown * 100)  # Convert to percentage
    
    except Exception as e:
        logger.error(f"Error calculating maximum drawdown: {str(e)}")
        return 0.0

def calculate_volatility(returns: Union[List[float], np.ndarray], 
                        periods_per_year: int = 252) -> float:
    """
    Calculate the annualized volatility
    
    Args:
        returns: List or array of returns
        periods_per_year: Number of periods in a year (default: 252 for daily returns)
        
    Returns:
        Annualized volatility as a percentage
    """
    try:
        if not isinstance(returns, np.ndarray):
            returns = np.array(returns)
        
        if len(returns) < 2:
            return 0.0
        
        # Calculate standard deviation
        std_dev = np.std(returns, ddof=1)  # Use sample standard deviation
        
        # Annualize volatility
        annualized_volatility = std_dev * np.sqrt(periods_per_year)
        
        return float(annualized_volatility * 100)  # Convert to percentage
    
    except Exception as e:
        logger.error(f"Error calculating volatility: {str(e)}")
        return 0.0

def calculate_cagr(values: Union[List[float], np.ndarray], 
                  periods: int, 
                  periods_per_year: int = 252) -> float:
    """
    Calculate the Compound Annual Growth Rate
    
    Args:
        values: List or array of portfolio values
        periods: Number of periods in the data
        periods_per_year: Number of periods in a year (default: 252 for daily returns)
        
    Returns:
        CAGR as a percentage
    """
    try:
        if not isinstance(values, np.ndarray):
            values = np.array(values)
        
        if len(values) < 2:
            return 0.0
        
        # Calculate total return
        total_return = values[-1] / values[0]
        
        # Calculate years
        years = periods / periods_per_year
        
        # Calculate CAGR
        cagr = (total_return ** (1 / years) - 1)
        
        return float(cagr * 100)  # Convert to percentage
    
    except Exception as e:
        logger.error(f"Error calculating CAGR: {str(e)}")
        return 0.0

def calculate_sortino_ratio(returns: Union[List[float], np.ndarray], 
                           risk_free_rate: float = 0.0, 
                           periods_per_year: int = 252) -> float:
    """
    Calculate the Sortino ratio (like Sharpe but only considering downside volatility)
    
    Args:
        returns: List or array of returns
        risk_free_rate: Annual risk-free rate (default: 0.0)
        periods_per_year: Number of periods in a year (default: 252 for daily returns)
        
    Returns:
        Sortino ratio
    """
    try:
        if not isinstance(returns, np.ndarray):
            returns = np.array(returns)
        
        if len(returns) < 2:
            return 0.0
        
        # Convert annual risk-free rate to per-period rate
        rf_per_period = (1 + risk_free_rate) ** (1 / periods_per_year) - 1
        
        # Calculate excess returns
        excess_returns = returns - rf_per_period
        
        # Calculate mean excess return
        mean_excess_return = np.mean(excess_returns)
        
        # Calculate downside deviation (standard deviation of negative excess returns)
        negative_returns = excess_returns[excess_returns < 0]
        
        if len(negative_returns) < 2:
            # If no negative returns, return a very high Sortino ratio
            return 100.0
        
        downside_deviation = np.std(negative_returns, ddof=1)
        
        if downside_deviation == 0:
            return 0.0
        
        # Calculate Sortino ratio and annualize
        sortino_ratio = mean_excess_return / downside_deviation
        annualized_sortino = sortino_ratio * np.sqrt(periods_per_year)
        
        return float(annualized_sortino)
    
    except Exception as e:
        logger.error(f"Error calculating Sortino ratio: {str(e)}")
        return 0.0

def calculate_calmar_ratio(returns: Union[List[float], np.ndarray], 
                          values: Union[List[float], np.ndarray], 
                          periods_per_year: int = 252) -> float:
    """
    Calculate the Calmar ratio (annualized return divided by max drawdown)
    
    Args:
        returns: List or array of returns
        values: List or array of portfolio values
        periods_per_year: Number of periods in a year (default: 252 for daily returns)
        
    Returns:
        Calmar ratio
    """
    try:
        if not isinstance(returns, np.ndarray):
            returns = np.array(returns)
            
        if not isinstance(values, np.ndarray):
            values = np.array(values)
        
        if len(returns) < 2 or len(values) < 2:
            return 0.0
        
        # Calculate annualized return
        annualized_return = np.mean(returns) * periods_per_year
        
        # Calculate max drawdown
        max_drawdown = calculate_max_drawdown(values) / 100  # Convert back to decimal
        
        if max_drawdown == 0:
            return 0.0
        
        # Calculate Calmar ratio
        calmar_ratio = annualized_return / max_drawdown
        
        return float(calmar_ratio)
    
    except Exception as e:
        logger.error(f"Error calculating Calmar ratio: {str(e)}")
        return 0.0

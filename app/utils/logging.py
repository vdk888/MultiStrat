import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(log_level=logging.INFO, log_to_file=True, log_dir="logs"):
    """
    Configure application logging
    
    Args:
        log_level: Logging level (default: INFO)
        log_to_file: Whether to log to file (default: True)
        log_dir: Directory for log files (default: 'logs')
    """
    # Create logs directory if it doesn't exist
    if log_to_file and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create timestamp for log file name
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"portfolio_system_{timestamp}.log")
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Define format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)
    console_handler.setFormatter(formatter)
    
    # Add console handler to root logger
    root_logger.addHandler(console_handler)
    
    # Add file handler if enabled
    if log_to_file:
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set up specific loggers
    loggers = [
        "app",
        "app.services",
        "app.database",
        "app.api",
        "app.core",
        "app.utils",
        "uvicorn",
        "sqlalchemy"
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        
        # SQLAlchemy and Uvicorn loggers can be noisy at DEBUG level
        if logger_name in ["sqlalchemy", "uvicorn"] and log_level == logging.DEBUG:
            logger.setLevel(logging.INFO)
    
    # Log startup message
    logging.info(f"Logging initialized at level {logging.getLevelName(log_level)}")
    if log_to_file:
        logging.info(f"Logging to file: {log_file}")
    
    return root_logger

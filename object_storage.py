"""
Object Storage Utility Functions

This module provides functionality for working with Replit Object Storage.
It provides consistent methods for storing and retrieving data across the application.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from replit.object_storage import Client as ObjectStorageClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ObjectStorageManager:
    """Manager class for Replit Object Storage operations"""
    
    def __init__(self):
        """Initialize the ObjectStorageManager with a Replit Object Storage client"""
        self.client = ObjectStorageClient()
    
    def save_to_storage(self, key: str, data: Any) -> bool:
        """
        Save data to Object Storage
        
        Args:
            key: The key to store the data under
            data: The data to store (will be JSON serialized)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            json_data = json.dumps(data, indent=4)
            self.client.upload_from_text(key, json_data)
            logger.info(f"Successfully saved data to Object Storage with key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error saving to Object Storage: {str(e)}")
            return False
    
    def load_from_storage(self, key: str) -> Optional[Dict]:
        """
        Load data from Object Storage
        
        Args:
            key: The key to load data from
            
        Returns:
            Optional[Dict]: The loaded data, or None if not found or error
        """
        try:
            json_content = self.client.download_as_text(key)
            data = json.loads(json_content)
            logger.info(f"Successfully loaded data from Object Storage with key: {key}")
            return data
        except Exception as e:
            logger.warning(f"Could not load from Object Storage for key {key}: {str(e)}")
            return None
    
    def save_best_params(self, symbol: str, best_params: Dict, metrics: Dict) -> bool:
        """
        Save best parameters for a symbol to Object Storage
        
        Args:
            symbol: The trading symbol
            best_params: The best parameters for the symbol
            metrics: Performance metrics for these parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load existing data
            data = self.load_from_storage("best_params.json") or {}
            
            # Create or update history
            history = []
            if symbol in data:
                # Check if the symbol has all required fields before updating history
                required_fields = ['best_params', 'metrics', 'date']
                if all(field in data[symbol] for field in required_fields):
                    # Get existing history or create new one
                    if 'history' in data[symbol]:
                        history = data[symbol]['history']
                    
                    # Append current best params to history
                    history.append({
                        'params': data[symbol]['best_params'],
                        'metrics': data[symbol]['metrics'],
                        'date': data[symbol]['date']
                    })
            
            # Update the symbol data with new best params and include history
            data[symbol] = {
                'best_params': best_params,
                'metrics': metrics,
                'date': datetime.now().strftime("%Y-%m-%d"),  # Add current date
                'history': history  # Include the history
            }
            
            # Save to Object Storage
            return self.save_to_storage("best_params.json", data)
        except Exception as e:
            logger.error(f"Error in save_best_params: {str(e)}")
            return False
    
    def get_best_params(self, symbol: str, default_params: Dict = None) -> Dict:
        """
        Get best parameters for a symbol from Object Storage
        
        Args:
            symbol: The trading symbol
            default_params: Default parameters to use if none found
            
        Returns:
            Dict: The best parameters or default parameters
        """
        try:
            data = self.load_from_storage("best_params.json")
            if data and symbol in data:
                logger.info(f"Found best parameters for {symbol} in Object Storage")
                return data[symbol]['best_params']
            else:
                logger.warning(f"No best parameters found for {symbol}")
                return default_params or {}
        except Exception as e:
            logger.error(f"Error in get_best_params: {str(e)}")
            return default_params or {}
    
    def get_all_symbols_params(self) -> Dict:
        """
        Get parameters for all symbols
        
        Returns:
            Dict: Dictionary with all symbol parameters
        """
        return self.load_from_storage("best_params.json") or {}
    
    def save_backup_to_file(self, key: str, data: Any = None) -> bool:
        """
        Save a backup of the Object Storage data to a local file
        
        Args:
            key: The key to backup
            data: The data to backup (if None, will load from Object Storage)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if data is None:
                data = self.load_from_storage(key)
                
            if data:
                with open(key, "w") as f:
                    json.dump(data, f, indent=4)
                logger.info(f"Successfully saved backup to file: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving backup to file: {str(e)}")
            return False
    
    def load_backup_from_file(self, key: str) -> Optional[Dict]:
        """
        Load backup data from a local file
        
        Args:
            key: The key/filename to load from
            
        Returns:
            Optional[Dict]: The loaded data, or None if not found or error
        """
        try:
            with open(key, "r") as f:
                data = json.load(f)
            logger.info(f"Successfully loaded backup from file: {key}")
            return data
        except Exception as e:
            logger.warning(f"Could not load backup from file {key}: {str(e)}")
            return None
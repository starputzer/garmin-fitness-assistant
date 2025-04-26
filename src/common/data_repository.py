import os
import json
import pandas as pd
from datetime import datetime


class GarminDataRepository:
    def __init__(self, storage_path):
        """
        Initialize the repository with a storage path.
        
        Args:
            storage_path (str): Path to directory for storing data.
        """
        self.storage_path = storage_path
        
        # Create directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Create subdirectories for different data types
        for data_type in ['race_predictions', 'training_history', 'metrics', 'activities']:
            os.makedirs(os.path.join(storage_path, data_type), exist_ok=True)
    
    def save_data(self, data_type, data, user_id=None):
        """
        Save data to the repository.
        
        Args:
            data_type (str): Type of data ('race_predictions', 'training_history', 'metrics', 'activities').
            data (pandas.DataFrame or dict): Data to save.
            user_id (str, optional): User identifier for multi-user support.
            
        Returns:
            str: Path to saved file.
        """
        if user_id is None:
            user_id = 'default'
        
        # Create user directory if it doesn't exist
        user_dir = os.path.join(self.storage_path, data_type, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Convert DataFrame to dict if necessary
        if isinstance(data, pd.DataFrame):
            data_dict = data.to_dict(orient='records')
        else:
            data_dict = data
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{data_type}_{timestamp}.json"
        filepath = os.path.join(user_dir, filename)
        
        # Save the data
        with open(filepath, 'w') as f:
            json.dump(data_dict, f, indent=2, default=str)
        
        return filepath
    
    def load_data(self, data_type, user_id=None, timestamp=None):
        """
        Load data from the repository.
        
        Args:
            data_type (str): Type of data to load.
            user_id (str, optional): User identifier.
            timestamp (str, optional): Specific timestamp to load.
                                      If None, loads the latest file.
        
        Returns:
            dict: Loaded data.
        """
        if user_id is None:
            user_id = 'default'
        
        user_dir = os.path.join(self.storage_path, data_type, user_id)
        
        if not os.path.exists(user_dir):
            return None
        
        # Get list of files
        files = [f for f in os.listdir(user_dir) if f.endswith('.json')]
        
        if not files:
            return None
        
        if timestamp is not None:
            # Find file with matching timestamp
            matching_files = [f for f in files if timestamp in f]
            if not matching_files:
                return None
            filename = matching_files[0]
        else:
            # Get the latest file
            files.sort(reverse=True)
            filename = files[0]
        
        filepath = os.path.join(user_dir, filename)
        
        # Load the data
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return data
    
    def list_available_data(self, user_id=None):
        """
        List available data in the repository.
        
        Args:
            user_id (str, optional): User identifier.
            
        Returns:
            dict: Dictionary of available data, organized by data type and timestamp.
        """
        if user_id is None:
            user_id = 'default'
        
        result = {}
        
        for data_type in ['race_predictions', 'training_history', 'metrics', 'activities']:
            user_dir = os.path.join(self.storage_path, data_type, user_id)
            
            if not os.path.exists(user_dir):
                continue
            
            files = [f for f in os.listdir(user_dir) if f.endswith('.json')]
            files.sort(reverse=True)
            
            if files:
                result[data_type] = files
        
        return result
    
    def delete_data(self, data_type, user_id=None, timestamp=None):
        """
        Delete data from the repository.
        
        Args:
            data_type (str): Type of data to delete.
            user_id (str, optional): User identifier.
            timestamp (str, optional): Specific timestamp to delete.
                                      If None, deletes the latest file.
        
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        if user_id is None:
            user_id = 'default'
        
        user_dir = os.path.join(self.storage_path, data_type, user_id)
        
        if not os.path.exists(user_dir):
            return False
        
        # Get list of files
        files = [f for f in os.listdir(user_dir) if f.endswith('.json')]
        
        if not files:
            return False
        
        if timestamp is not None:
            # Find file with matching timestamp
            matching_files = [f for f in files if timestamp in f]
            if not matching_files:
                return False
            filename = matching_files[0]
        else:
            # Get the latest file
            files.sort(reverse=True)
            filename = files[0]
        
        filepath = os.path.join(user_dir, filename)
        
        # Delete the file
        try:
            os.remove(filepath)
            return True
        except:
            return False
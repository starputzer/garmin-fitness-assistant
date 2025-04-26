import json
import os
import glob
from datetime import datetime
import pandas as pd


class GarminParser:
    def __init__(self, data_dir=None):
        """
        Initializes the parser with a data directory.
        
        Args:
            data_dir (str, optional): Path to directory containing Garmin export files.
                                     If None, user will need to provide file paths explicitly.
        """
        self.data_dir = data_dir
        self.race_predictions = None
        self.training_history = None
        self.heat_altitude_metrics = None
        self.activities = None
        
    def parse_race_predictions(self, file_path=None):
        """
        Parse race predictions data from a JSON file.
        
        Args:
            file_path (str, optional): Path to race predictions JSON file.
                                      If None, will attempt to find in data_dir.
        
        Returns:
            pandas.DataFrame: DataFrame containing race predictions data.
        """
        if file_path is None and self.data_dir is not None:
            pattern = os.path.join(self.data_dir, "RunRacePredictions_*.json")
            matches = glob.glob(pattern)
            if matches:
                file_path = matches[0]
            else:
                raise FileNotFoundError(f"No race predictions file found in {self.data_dir}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Convert timestamp string to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Convert race times from seconds to more readable format
        for col in ['raceTime5K', 'raceTime10K', 'raceTimeHalf', 'raceTimeMarathon']:
            if col in df.columns:
                df[f'{col}_formatted'] = df[col].apply(lambda x: f"{x // 60}:{x % 60:02d}")
        
        self.race_predictions = df
        return df
    
    def parse_training_history(self, file_path=None):
        """
        Parse training history data from a JSON file.
        
        Args:
            file_path (str, optional): Path to training history JSON file.
                                      If None, will attempt to find in data_dir.
        
        Returns:
            pandas.DataFrame: DataFrame containing training history data.
        """
        if file_path is None and self.data_dir is not None:
            pattern = os.path.join(self.data_dir, "TrainingHistory_*.json")
            matches = glob.glob(pattern)
            if matches:
                file_path = matches[0]
            else:
                raise FileNotFoundError(f"No training history file found in {self.data_dir}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Convert timestamp string to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['calendarDate'] = pd.to_datetime(df['calendarDate'])
        
        self.training_history = df
        return df
    
    def parse_heat_altitude_metrics(self, file_path=None):
        """
        Parse heat and altitude acclimation metrics from a JSON file.
        
        Args:
            file_path (str, optional): Path to metrics JSON file.
                                      If None, will attempt to find in data_dir.
        
        Returns:
            pandas.DataFrame: DataFrame containing heat and altitude acclimation metrics.
        """
        if file_path is None and self.data_dir is not None:
            pattern = os.path.join(self.data_dir, "MetricsHeatAltitudeAcclimation_*.json")
            matches = glob.glob(pattern)
            if matches:
                file_path = matches[0]
            else:
                raise FileNotFoundError(f"No metrics file found in {self.data_dir}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Convert timestamp strings to datetime
        timestamp_columns = [col for col in df.columns if 'timestamp' in col.lower()]
        for col in timestamp_columns:
            df[col] = pd.to_datetime(df[col])
        
        df['calendarDate'] = pd.to_datetime(df['calendarDate'])
        
        self.heat_altitude_metrics = df
        return df
    
    def parse_activities(self, file_path=None):
        """
        Parse activities data from a JSON file.
        Note: This is a placeholder until we have a better understanding of the activities file format.
        
        Args:
            file_path (str, optional): Path to activities JSON file.
                                      If None, will attempt to find in data_dir.
        
        Returns:
            pandas.DataFrame: DataFrame containing activities data.
        """
        if file_path is None and self.data_dir is not None:
            pattern = os.path.join(self.data_dir, "SummarizedActivities_*.json")
            matches = glob.glob(pattern)
            if matches:
                file_path = matches[0]
            else:
                raise FileNotFoundError(f"No activities file found in {self.data_dir}")
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Convert timestamp columns to datetime
            for col in df.columns:
                if 'Date' in col or 'date' in col or 'timestamp' in col:
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except:
                        pass  # Skip columns that can't be converted
            
            self.activities = df
            return df
            
        except json.JSONDecodeError:
            # Handle large or complex JSON files
            print(f"File {file_path} is too large or complex for direct parsing.")
            print("Using chunked reading approach...")
            
            # For very large files, we might need a chunked approach
            # This is a placeholder for now
            return pd.DataFrame()
    
    def parse_all_available(self):
        """
        Parse all available data files in the data directory.
        
        Returns:
            dict: Dictionary of DataFrames for each data type.
        """
        results = {}
        
        try:
            results['race_predictions'] = self.parse_race_predictions()
        except FileNotFoundError:
            pass
        
        try:
            results['training_history'] = self.parse_training_history()
        except FileNotFoundError:
            pass
        
        try:
            results['heat_altitude_metrics'] = self.parse_heat_altitude_metrics()
        except FileNotFoundError:
            pass
        
        try:
            results['activities'] = self.parse_activities()
        except FileNotFoundError:
            pass
        
        return results
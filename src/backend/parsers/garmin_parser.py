import json
import os
import glob
import re
from datetime import datetime
import pandas as pd
import logging
from pathlib import Path

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("GarminParser")

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
            # Erweiterte und rekursive Suche in allen Unterordnern
            patterns = [
                os.path.join(self.data_dir, "**", "*RunRacePredictions*.json"),
            ]
            
            # Durchsuche alle Muster rekursiv
            file_path = None
            for pattern in patterns:
                matches = glob.glob(pattern, recursive=True)
                if matches:
                    # Nehme die neueste Datei basierend auf dem Dateinamen
                    matches.sort(reverse=True)
                    file_path = matches[0]
                    logger.info(f"Found race predictions file: {file_path}")
                    break
            
            if file_path is None:
                raise FileNotFoundError(f"No race predictions file found in {self.data_dir}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Convert timestamp string to datetime
        if 'timestamp' in df.columns:
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
            # Rekursive Suche in allen Unterordnern
            patterns = [
                os.path.join(self.data_dir, "**", "*TrainingHistory*.json"),
                os.path.join(self.data_dir, "**", "*EnduranceScore*.json"),  # Alternative
            ]
            
            # Zuerst nach TrainingHistory, dann nach EnduranceScore suchen
            file_path = None
            
            # TrainingHistory prioritär suchen
            for pattern in patterns:
                matches = glob.glob(pattern, recursive=True)
                if matches:
                    # Filtere nach bestimmten Mustern:
                    # - TrainingHistory bevorzugen
                    # - EnduranceScore nur als Fallback
                    preferred_matches = [m for m in matches if "TrainingHistory" in m]
                    if preferred_matches:
                        matches = preferred_matches
                        
                    # Nehme die neueste Datei basierend auf dem Dateinamen
                    matches.sort(reverse=True)
                    file_path = matches[0]
                    logger.info(f"Found training history file: {file_path}")
                    break
            
            if file_path is None:
                raise FileNotFoundError(f"No training history file found in {self.data_dir}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Fix date issues for Endurance Score
        if 'EnduranceScore' in Path(file_path).name:
            # Datum aus dem Dateinamen extrahieren
            # Format: EnduranceScore_20250323_20250701_72702010.json
            date_parts = re.findall(r'_(\d{8})_', Path(file_path).name)
            if date_parts:
                start_date_str = date_parts[0]
                try:
                    # YYYYMMDD Format
                    start_date = pd.to_datetime(start_date_str, format='%Y%m%d')
                    logger.info(f"Using date from filename: {start_date}")
                    
                    # Da wir keine echten Datumsinformationen haben, verwenden wir Daten aus dem Dateinamen
                    # und verteilen sie über den Zeitraum
                    num_rows = len(df)
                    if num_rows > 1:
                        # Erstelle einen Datums-Range
                        date_range = pd.date_range(start=start_date, periods=num_rows)
                        df['timestamp'] = date_range
                        df['calendarDate'] = date_range
                    else:
                        df['timestamp'] = start_date
                        df['calendarDate'] = start_date
                except Exception as e:
                    logger.warning(f"Error creating dates from filename: {e}")
                    # Fallback zu aktuellen Datum
                    df['timestamp'] = pd.Timestamp.now()
                    df['calendarDate'] = pd.Timestamp.now()
            else:
                # Kein Datum im Dateinamen gefunden
                logger.warning("No date found in filename, using current date")
                df['timestamp'] = pd.Timestamp.now()
                df['calendarDate'] = pd.Timestamp.now()
                
            # Trainingsstatus für Endurance-Daten erzeugen
            if 'enduranceScore' in df.columns:
                df['trainingStatus'] = df['enduranceScore'].apply(
                    lambda x: 'productive' if x > 80 else 
                             ('maintaining' if x > 60 else 
                             ('recovery' if x > 40 else 'unproductive'))
                )
            elif 'score' in df.columns:
                df['trainingStatus'] = df['score'].apply(
                    lambda x: 'productive' if x > 80 else 
                             ('maintaining' if x > 60 else 
                             ('recovery' if x > 40 else 'unproductive'))
                )
            else:
                # Standardwert
                df['trainingStatus'] = 'maintaining'
        else:
            # Standardmäßige Zeitstempelkonvertierung für normale Trainingsdaten
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            if 'calendarDate' in df.columns:
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
            # Rekursive Suche in allen Unterordnern
            patterns = [
                os.path.join(self.data_dir, "**", "*MetricsHeatAltitude*.json"),
                os.path.join(self.data_dir, "**", "*MetricsAcuteTrainingLoad*.json"),  # Alternative
            ]
            
            # Durchsuche alle Muster rekursiv
            file_path = None
            
            # MetricsHeatAltitude prioritär suchen
            for pattern in patterns:
                matches = glob.glob(pattern, recursive=True)
                if matches:
                    # Filtere nach bestimmten Mustern
                    preferred_matches = [m for m in matches if "MetricsHeatAltitude" in m]
                    if preferred_matches:
                        matches = preferred_matches
                        
                    # Nehme die neueste Datei basierend auf dem Dateinamen
                    matches.sort(reverse=True)
                    file_path = matches[0]
                    logger.info(f"Found metrics file: {file_path}")
                    break
            
            if file_path is None:
                raise FileNotFoundError(f"No metrics file found in {self.data_dir}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Ähnliche Datumskorrektur wie bei Training History
        if 'MetricsAcuteTrainingLoad' in Path(file_path).name:
            # Datum aus dem Dateinamen extrahieren
            # Format: MetricsAcuteTrainingLoad_20250323_20250701_72702010.json
            date_parts = re.findall(r'_(\d{8})_', Path(file_path).name)
            if date_parts:
                start_date_str = date_parts[0]
                try:
                    start_date = pd.to_datetime(start_date_str, format='%Y%m%d')
                    logger.info(f"Using date from filename: {start_date}")
                    
                    num_rows = len(df)
                    if num_rows > 1:
                        date_range = pd.date_range(start=start_date, periods=num_rows)
                        df['timestamp'] = date_range
                        df['calendarDate'] = date_range
                    else:
                        df['timestamp'] = start_date
                        df['calendarDate'] = start_date
                except Exception as e:
                    logger.warning(f"Error creating dates from filename: {e}")
                    df['timestamp'] = pd.Timestamp.now()
                    df['calendarDate'] = pd.Timestamp.now()
            else:
                logger.warning("No date found in filename, using current date")
                df['timestamp'] = pd.Timestamp.now()
                df['calendarDate'] = pd.Timestamp.now()
        else:
            # Standardmäßige Zeitstempelkonvertierung
            timestamp_columns = [col for col in df.columns if 'timestamp' in col.lower()]
            for col in timestamp_columns:
                df[col] = pd.to_datetime(df[col])
            
            if 'calendarDate' in df.columns:
                df['calendarDate'] = pd.to_datetime(df['calendarDate'])
        
        self.heat_altitude_metrics = df
        return df
    
    def find_all_activities_files(self):
        """Find all activities files in the Garmin export directory."""
        if self.data_dir is None:
            raise ValueError("No data directory specified")
            
        # Suche rekursiv nach allen Aktivitätsdateien
        patterns = [
            os.path.join(self.data_dir, "**", "*summarizedActivities*.json"),
        ]
        
        all_matches = []
        for pattern in patterns:
            matches = glob.glob(pattern, recursive=True)
            all_matches.extend(matches)
        
        # Eindeutige Dateien
        all_matches = list(set(all_matches))
        
        return all_matches
    
    def parse_activities(self, file_path=None):
        """
        Parse activities data from a JSON file.
        
        Args:
            file_path (str, optional): Path to activities JSON file.
                                      If None, will attempt to find in data_dir.
        
        Returns:
            pandas.DataFrame: DataFrame containing activities data.
        """
        if file_path is None and self.data_dir is not None:
            # Finde alle Aktivitätsdateien
            all_matches = self.find_all_activities_files()
            
            if not all_matches:
                raise FileNotFoundError(f"No activities file found in {self.data_dir}")
            
            # Nehme die neueste Datei
            all_matches.sort(reverse=True)
            file_path = all_matches[0]
            logger.info(f"Using activities file: {file_path}")
        
        try:
            logger.info(f"Parsing activities file: {file_path}")
            file_size = os.path.getsize(file_path)
            logger.info(f"Activities file size: {file_size / (1024*1024):.2f} MB")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                # Lade die gesamte Datei
                data = json.load(f)
                
                # Überprüfe, ob es sich um das spezielle Format mit summarizedActivitiesExport handelt
                if isinstance(data, list) and len(data) > 0 and 'summarizedActivitiesExport' in data[0]:
                    # Extrahiere das innere Array aus summarizedActivitiesExport
                    activities_data = data[0]['summarizedActivitiesExport']
                    logger.info(f"Found {len(activities_data)} activities in summarizedActivitiesExport format")
                else:
                    # Standard-Format
                    activities_data = data
                    logger.info(f"Found {len(activities_data)} activities in standard format")
            
                # Konvertiere zu DataFrame
                df = pd.DataFrame(activities_data)
                
                # Konvertiere Zeitstempel
                timestamp_columns = ['beginTimestamp', 'startTimeGmt', 'startTimeLocal', 
                                    'lastUpdateTimestamp', 'beginTimestampGMT', 'endTimestampGMT']
                
                for col in timestamp_columns:
                    if col in df.columns:
                        try:
                            # Für Unix-Millisekunden-Zeitstempel
                            if df[col].dtype in [int, float]:
                                df[col] = pd.to_datetime(df[col], unit='ms')
                            else:
                                df[col] = pd.to_datetime(df[col])
                        except Exception as e:
                            logger.warning(f"Error converting {col} to datetime: {e}")
                
                # Zusätzliche Konversionen für andere Datum/Zeit-Felder
                for col in df.columns:
                    if any(time_part in col.lower() for time_part in ['date', 'time', 'timestamp']) and col not in timestamp_columns:
                        try:
                            df[col] = pd.to_datetime(df[col])
                        except Exception as e:
                            logger.debug(f"Could not convert {col} to datetime: {e}")
                
                return df
        except Exception as e:
            logger.error(f"Error parsing activities file: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
    
    def parse_all_activities(self):
        """Parse all available activities files and combine them into a single DataFrame."""
        if self.data_dir is None:
            raise ValueError("No data directory specified")
            
        # Finde alle Aktivitätsdateien
        all_matches = self.find_all_activities_files()
        
        if not all_matches:
            raise FileNotFoundError(f"No activities files found in {self.data_dir}")
        
        logger.info(f"Found {len(all_matches)} activities files: {all_matches}")
        
        # Parse jede Datei und sammle die Daten
        all_activities = []
        total_activities = 0
        
        for file_path in all_matches:
            try:
                df = self.parse_activities(file_path)
                if df is not None and not df.empty:
                    logger.info(f"Successfully parsed {len(df)} activities from {file_path}")
                    all_activities.append(df)
                    total_activities += len(df)
                else:
                    logger.warning(f"No activities found in {file_path}")
            except Exception as e:
                logger.error(f"Error parsing {file_path}: {e}")
        
        # Kombiniere alle DataFrames
        if all_activities:
            combined_df = pd.concat(all_activities, ignore_index=True)
            logger.info(f"Combined {len(combined_df)} activities from {len(all_activities)} files")
            
            # Entferne Duplikate basierend auf activityId, falls vorhanden
            if 'activityId' in combined_df.columns:
                before_count = len(combined_df)
                combined_df = combined_df.drop_duplicates(subset=['activityId'])
                after_count = len(combined_df)
                if before_count != after_count:
                    logger.info(f"Removed {before_count - after_count} duplicate activities")
            
            self.activities = combined_df
            return combined_df
        else:
            logger.warning("No activities found in any file")
            return pd.DataFrame()
    
    def parse_all_available(self):
        """
        Parse all available data files in the data directory, combining historical data.
        
        Returns:
            dict: Dictionary of DataFrames for each data type.
        """
        results = {}
        
        # Race Predictions - alle Dateien kombinieren
        try:
            race_pred_files = glob.glob(os.path.join(self.data_dir, "**", "*RunRacePredictions*.json"), recursive=True)
            if race_pred_files:
                all_race_predictions = []
                for file in race_pred_files:
                    try:
                        df = self.parse_race_predictions(file)
                        if df is not None and not df.empty:
                            logger.info(f"Parsed race predictions from {file}: {len(df)} records")
                            all_race_predictions.append(df)
                    except Exception as e:
                        logger.warning(f"Error parsing {file}: {e}")
                
                if all_race_predictions:
                    combined_df = pd.concat(all_race_predictions, ignore_index=True)
                    combined_df = combined_df.drop_duplicates()  # Entferne Duplikate
                    results['race_predictions'] = combined_df
                    logger.info(f"Combined {len(combined_df)} race prediction records from {len(race_pred_files)} files")
        except Exception as e:
            logger.warning(f"Error processing race predictions: {e}")
        
        # Training History - alle Dateien kombinieren
        try:
            training_files = glob.glob(os.path.join(self.data_dir, "**", "*TrainingHistory*.json"), recursive=True)
            if training_files:
                all_training = []
                for file in training_files:
                    try:
                        df = self.parse_training_history(file)
                        if df is not None and not df.empty:
                            logger.info(f"Parsed training history from {file}: {len(df)} records")
                            all_training.append(df)
                    except Exception as e:
                        logger.warning(f"Error parsing {file}: {e}")
                
                if all_training:
                    combined_df = pd.concat(all_training, ignore_index=True)
                    combined_df = combined_df.drop_duplicates()  # Entferne Duplikate
                    results['training_history'] = combined_df
                    logger.info(f"Combined {len(combined_df)} training history records from {len(training_files)} files")
        except Exception as e:
            logger.warning(f"Error processing training history: {e}")
        
        # Heat Altitude Metrics - alle Dateien kombinieren
        try:
            metrics_files = glob.glob(os.path.join(self.data_dir, "**", "*MetricsHeatAltitude*.json"), recursive=True)
            if metrics_files:
                all_metrics = []
                for file in metrics_files:
                    try:
                        df = self.parse_heat_altitude_metrics(file)
                        if df is not None and not df.empty:
                            logger.info(f"Parsed metrics from {file}: {len(df)} records")
                            all_metrics.append(df)
                    except Exception as e:
                        logger.warning(f"Error parsing {file}: {e}")
                
                if all_metrics:
                    combined_df = pd.concat(all_metrics, ignore_index=True)
                    combined_df = combined_df.drop_duplicates()  # Entferne Duplikate
                    results['heat_altitude_metrics'] = combined_df
                    logger.info(f"Combined {len(combined_df)} metrics records from {len(metrics_files)} files")
        except Exception as e:
            logger.warning(f"Error processing metrics: {e}")
        
        # Activities - verwende parse_all_activities für alle Aktivitätsdateien
        try:
            results['activities'] = self.parse_all_activities()
        except Exception as e:
            logger.warning(f"Error processing activities: {e}")
        
        return results
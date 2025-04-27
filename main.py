import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import logging
import getpass
import datetime

# Ensure the project root is in the Python path
sys.path.append(str(Path(__file__).parent))

from src.backend.parsers.garmin_parser import GarminParser
from src.backend.analysis.run_analyzer import RunAnalyzer
from src.common.data_repository import GarminDataRepository

# Import the new Garmin connector
try:
    from src.backend.connectors.garmin_connect import GarminConnector
    GARMIN_CONNECT_AVAILABLE = True
except ImportError:
    GARMIN_CONNECT_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("GarminAssistant")

def parse_args():
    parser = argparse.ArgumentParser(description='Garmin Fitness Assistant')
    
    # Datei- und Verzeichnisoptionen
    parser.add_argument('--data-dir', type=str, help='Directory containing Garmin export files')
    parser.add_argument('--storage-dir', type=str, default='./data/storage', help='Directory for storing processed data')
    parser.add_argument('--predictions-file', type=str, help='Path to race predictions JSON file')
    parser.add_argument('--training-file', type=str, help='Path to training history JSON file')
    parser.add_argument('--metrics-file', type=str, help='Path to metrics JSON file')
    parser.add_argument('--activities-file', type=str, help='Path to activities JSON file')
    
    # Analyseoptionen
    parser.add_argument('--analyze', action='store_true', help='Perform analysis after parsing')
    parser.add_argument('--historical', action='store_true', help='Process all historical data files')
    
    # Garmin Connect API-Optionen
    if GARMIN_CONNECT_AVAILABLE:
        parser.add_argument('--connect', action='store_true', help='Connect to Garmin Connect API instead of using files')
        parser.add_argument('--username', type=str, help='Garmin Connect username (email)')
        parser.add_argument('--password', type=str, help='Garmin Connect password (will prompt if not provided)')
        parser.add_argument('--start-date', type=str, help='Start date for data retrieval (YYYY-MM-DD)')
        parser.add_argument('--end-date', type=str, help='End date for data retrieval (YYYY-MM-DD)')
        parser.add_argument('--cache-dir', type=str, default='./data/cache', help='Directory for caching API results')
        parser.add_argument('--health-data', action='store_true', help='Also retrieve health data (sleep, stress, heart rate)')
    
    return parser.parse_args()

def get_data_from_files(parser, args):
    """Daten aus Dateien laden"""
    data = {}
    
    try:
        if args.predictions_file:
            data['race_predictions'] = parser.parse_race_predictions(args.predictions_file)
        elif args.data_dir:
            try:
                data['race_predictions'] = parser.parse_race_predictions()
            except FileNotFoundError:
                logger.warning("Race predictions file not found.")
        
        if args.training_file:
            data['training_history'] = parser.parse_training_history(args.training_file)
        elif args.data_dir:
            try:
                data['training_history'] = parser.parse_training_history()
            except FileNotFoundError:
                logger.warning("Training history file not found.")
        
        if args.metrics_file:
            data['heat_altitude_metrics'] = parser.parse_heat_altitude_metrics(args.metrics_file)
        elif args.data_dir:
            try:
                data['heat_altitude_metrics'] = parser.parse_heat_altitude_metrics()
            except FileNotFoundError:
                logger.warning("Heat/altitude metrics file not found.")
        
        if args.activities_file:
            data['activities'] = parser.parse_activities(args.activities_file)
        elif args.data_dir:
            try:
                # Use parse_all_activities to get all activities files, even in non-historical mode
                data['activities'] = parser.parse_all_activities()
            except FileNotFoundError:
                logger.warning("Activities file not found.")
                
    except Exception as e:
        logger.error(f"Error parsing data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
        
    return data

def get_data_from_garmin_connect(args):
    """Daten direkt von Garmin Connect API abrufen"""
    if not GARMIN_CONNECT_AVAILABLE:
        logger.error("Garmin Connect integration not available. Install garminconnect package.")
        return {}
    
    # Username und Passwort überprüfen
    username = args.username
    password = args.password
    
    if not username:
        username = input("Garmin Connect Username (Email): ")
    
    if not password:
        password = getpass.getpass("Garmin Connect Password: ")
    
    if not username or not password:
        logger.error("Username and password are required for Garmin Connect")
        return {}
    
    # Start- und Enddatum bestimmen
    end_date = args.end_date or datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Standardmäßig 90 Tage zurück, oder das angegebene Startdatum
    if args.start_date:
        start_date = args.start_date
    else:
        start_date = (datetime.datetime.strptime(end_date, "%Y-%m-%d") - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
    
    # Cache-Verzeichnis erstellen
    os.makedirs(args.cache_dir, exist_ok=True)
    
    try:
        # Mit Garmin Connect verbinden
        connector = GarminConnector(username, password, cache_dir=args.cache_dir)
        connector.connect()
        
        logger.info("Erfolgreich mit Garmin Connect verbunden!")
        
        data = {}
        
        # Daten abrufen
        logger.info(f"Rufe Daten von Garmin Connect für Zeitraum {start_date} bis {end_date} ab...")
        
        # Aktivitäten abrufen
        try:
            activities = connector.get_activities(start_date=start_date, end_date=end_date)
            if not activities.empty:
                data['activities'] = activities
                logger.info(f"  - {len(activities)} Aktivitäten abgerufen")
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von Aktivitäten: {e}")
        
        # Rennprognosen abrufen/generieren
        try:
            race_predictions = connector.get_race_predictions()
            if not race_predictions.empty:
                data['race_predictions'] = race_predictions
                logger.info(f"  - {len(race_predictions)} Rennprognosen erstellt")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen von Rennprognosen: {e}")
        
        # Trainingsstatus erstellen
        try:
            training_history = connector.get_training_history()
            if not training_history.empty:
                data['training_history'] = training_history
                logger.info(f"  - {len(training_history)} Trainingshistorie-Einträge erstellt")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Trainingshistorie: {e}")
        
        # Hitze- und Höhenakklimatisierung erstellen
        try:
            heat_altitude = connector.get_heat_altitude_metrics()
            if not heat_altitude.empty:
                data['heat_altitude_metrics'] = heat_altitude
                logger.info(f"  - {len(heat_altitude)} Hitze- und Höhenakklimatisierungseinträge erstellt")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Hitze- und Höhenakklimatisierungsdaten: {e}")
        
        # Gesundheitsdaten abrufen, wenn angefordert
        if args.health_data:
            logger.info("Rufe Gesundheitsdaten ab...")
            
            # Gewichtsdaten
            try:
                weight_data = connector.get_weight_data(start_date=start_date, end_date=end_date)
                if not weight_data.empty:
                    data['weight_data'] = weight_data
                    logger.info(f"  - {len(weight_data)} Gewichtsdaten abgerufen")
            except Exception as e:
                logger.error(f"Fehler beim Abrufen der Gewichtsdaten: {e}")
            
            # Herzfrequenzdaten
            try:
                heart_rate_data = connector.get_heart_rates(
                    start_date=max(start_date, (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")),
                    end_date=end_date
                )
                if not heart_rate_data.empty:
                    data['heart_rate_data'] = heart_rate_data
                    logger.info(f"  - {len(heart_rate_data)} Herzfrequenzdaten abgerufen")
            except Exception as e:
                logger.error(f"Fehler beim Abrufen der Herzfrequenzdaten: {e}")
            
            # Schlafdaten
            try:
                sleep_data = connector.get_sleep_data(
                    start_date=max(start_date, (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")),
                    end_date=end_date
                )
                if not sleep_data.empty:
                    data['sleep_data'] = sleep_data
                    logger.info(f"  - {len(sleep_data)} Schlafdaten abgerufen")
            except Exception as e:
                logger.error(f"Fehler beim Abrufen der Schlafdaten: {e}")
            
            # Stressdaten
            try:
                stress_data = connector.get_stress_data(
                    start_date=max(start_date, (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")),
                    end_date=end_date
                )
                if not stress_data.empty:
                    data['stress_data'] = stress_data
                    logger.info(f"  - {len(stress_data)} Stressdaten abgerufen")
            except Exception as e:
                logger.error(f"Fehler beim Abrufen der Stressdaten: {e}")
            
            # Metriken (VO2Max, etc.)
            try:
                metrics_data = connector.get_metrics_data(start_date=start_date, end_date=end_date)
                if metrics_data:
                    data['metrics_data'] = metrics_data
                    logger.info("  - Trainingsmetriken abgerufen")
            except Exception as e:
                logger.error(f"Fehler beim Abrufen der Trainingsmetriken: {e}")
        
        return data
    
    except Exception as e:
        logger.error(f"Fehler bei der Verbindung zu Garmin Connect: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {}

def main():
    args = parse_args()
    
    # Check if we're using Garmin Connect API or files
    if GARMIN_CONNECT_AVAILABLE and args.connect:
        # Get data from Garmin Connect API
        logger.info("Verwende Garmin Connect API zur Datenabfrage")
        data = get_data_from_garmin_connect(args)
    else:
        # Check if data directory or individual files are provided
        if not args.data_dir and not (args.predictions_file or args.training_file or args.metrics_file or args.activities_file):
            logger.error("Error: Either --data-dir or specific file paths must be provided.")
            return 1
        
        # Initialize parser
        parser = GarminParser(data_dir=args.data_dir)
        
        # Parse available data from files
        if args.historical and args.data_dir:
            # Use the enhanced parse_all_available method to process all historical data
            logger.info("Processing all historical data files...")
            data = parser.parse_all_available()
        else:
            # Process individual files or just the latest files
            data = get_data_from_files(parser, args)
    
    # Initialize data repository
    repository = GarminDataRepository(storage_path=args.storage_dir)
    
    # Save parsed data to repository
    for data_type, df in data.items():
        if df is not None and not df.empty:
            repository.save_data(data_type, df)
            logger.info(f"Saved {len(df)} records to {data_type}")
    
    # Print summary of loaded data
    print("\n=== Garmin Fitness Assistant ===")
    for data_type, df in data.items():
        if df is not None and not df.empty:
            print(f"\n{data_type.replace('_', ' ').title()}:")
            print(f"  - {len(df)} records")
            if 'timestamp' in df.columns:
                print(f"  - Date range: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")
            elif 'date' in df.columns:
                print(f"  - Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    
    # Perform analysis if requested
    if args.analyze and 'race_predictions' in data and data['race_predictions'] is not None:
        analyzer = RunAnalyzer(
            data.get('race_predictions'), 
            data.get('training_history')
        )
        
        print("\n=== Latest Race Predictions ===")
        latest = analyzer.get_latest_predictions()
        for race, time in latest.items():
            print(f"{race}: {time}")
        
        print("\n=== Improvement Analysis ===")
        for distance in ['5K', '10K', 'Half', 'Marathon']:
            try:
                improvement = analyzer.calculate_improvement(distance)
                if 'insufficient_data' in improvement:
                    print(f"{distance}: {improvement['message']}")
                else:
                    change = "improved" if improvement['improved'] else "worsened"
                    print(f"{distance}: {improvement['time_diff_seconds']:.2f}s ({improvement['percent_improvement']:.2f}%) {change}")
                    print(f"  From {improvement['start_time']} to {improvement['end_time']}")
            except Exception as e:
                print(f"{distance}: Error analyzing - {e}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
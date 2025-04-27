import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import logging
import getpass
import datetime
import json

# Ensure the project root is in the Python path
sys.path.append(str(Path(__file__).parent))

from src.backend.parsers.garmin_parser import GarminParser
from src.backend.analysis.run_analyzer import RunAnalyzer
from src.common.data_repository import GarminDataRepository

# Import the Garmin connector
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
    
    # File and directory options
    parser.add_argument('--data-dir', type=str, help='Directory containing Garmin export files')
    parser.add_argument('--storage-dir', type=str, default='./data/storage', help='Directory for storing processed data')
    parser.add_argument('--predictions-file', type=str, help='Path to race predictions JSON file')
    parser.add_argument('--training-file', type=str, help='Path to training history JSON file')
    parser.add_argument('--metrics-file', type=str, help='Path to metrics JSON file')
    parser.add_argument('--activities-file', type=str, help='Path to activities JSON file')
    
    # Analysis options
    parser.add_argument('--analyze', action='store_true', help='Perform analysis after parsing')
    parser.add_argument('--historical', action='store_true', help='Process all historical data files')
    
    # Garmin Connect API options
    if GARMIN_CONNECT_AVAILABLE:
        parser.add_argument('--connect', action='store_true', help='Connect to Garmin Connect API instead of using files')
        parser.add_argument('--username', type=str, help='Garmin Connect username (email)')
        parser.add_argument('--password', type=str, help='Garmin Connect password (will prompt if not provided)')
        parser.add_argument('--start-date', type=str, help='Start date for data retrieval (YYYY-MM-DD), defaults to 2010-01-01')
        parser.add_argument('--end-date', type=str, help='End date for data retrieval (YYYY-MM-DD)')
        parser.add_argument('--cache-dir', type=str, default='./data/cache', help='Directory for caching API results')
        parser.add_argument('--health-data', action='store_true', help='Also retrieve health data (sleep, stress, heart rate)')
        parser.add_argument('--detailed-activities', action='store_true', help='Retrieve detailed activity data (GPS tracks, heart rate)')
        parser.add_argument('--activity-limit', type=int, help='Limit the number of activities to fetch details for (0=no limit)')
        parser.add_argument('--body-composition', action='store_true', help='Retrieve detailed body composition data')
        parser.add_argument('--stats-history', action='store_true', help='Retrieve long-term statistics and trends')
        parser.add_argument('--full', action='store_true', help='Retrieve all available data (equivalent to --health-data --detailed-activities --body-composition --stats-history with no activity limit)')
    
    return parser.parse_args()

def get_data_from_files(parser, args):
    """Load data from files"""
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
    """Retrieve data directly from Garmin Connect API"""
    if not GARMIN_CONNECT_AVAILABLE:
        logger.error("Garmin Connect integration not available. Install garminconnect package.")
        return {}
    
    # Check username and password
    username = args.username
    password = args.password
    
    if not username:
        username = input("Garmin Connect Username (Email): ")
    
    if not password:
        password = getpass.getpass("Garmin Connect Password: ")
    
    if not username or not password:
        logger.error("Username and password are required for Garmin Connect")
        return {}
    
    # Determine start and end dates
    end_date = args.end_date or datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Default to January 1, 2010 (or earlier if needed) to get all historical data
    # Change this date to match when you first started using Garmin devices
    if args.start_date:
        start_date = args.start_date
    else:
        start_date = "2010-01-01"  # Very early date to ensure all data is captured
    
    # Create cache directory
    os.makedirs(args.cache_dir, exist_ok=True)
    
    try:
        # Connect to Garmin Connect
        connector = GarminConnector(username, password, cache_dir=args.cache_dir)
        connector.connect()
        
        logger.info("Successfully connected to Garmin Connect!")
        
        data = {}
        
        # Retrieve data
        logger.info(f"Retrieving data from Garmin Connect for period {start_date} to {end_date}...")
        
        # Retrieve activities
        try:
            activities = connector.get_activities(start_date=start_date, end_date=end_date)
            if not activities.empty:
                data['activities'] = activities
                logger.info(f"  - {len(activities)} activities retrieved")
        except Exception as e:
            logger.error(f"Error retrieving activities: {e}")
        
        # Create/retrieve race predictions
        try:
            race_predictions = connector.get_race_predictions()
            if not race_predictions.empty:
                data['race_predictions'] = race_predictions
                logger.info(f"  - {len(race_predictions)} race predictions created")
        except Exception as e:
            logger.error(f"Error creating race predictions: {e}")
        
        # Create training history
        try:
            training_history = connector.get_training_history()
            if not training_history.empty:
                data['training_history'] = training_history
                logger.info(f"  - {len(training_history)} training history entries created")
        except Exception as e:
            logger.error(f"Error creating training history: {e}")
        
        # Create heat and altitude acclimatization
        try:
            heat_altitude = connector.get_heat_altitude_metrics()
            if not heat_altitude.empty:
                data['heat_altitude_metrics'] = heat_altitude
                logger.info(f"  - {len(heat_altitude)} heat and altitude acclimatization entries created")
        except Exception as e:
            logger.error(f"Error creating heat and altitude acclimatization data: {e}")
        
        # Check if we should retrieve all data (--full flag)
        if args.full:
            args.health_data = True
            args.detailed_activities = True
            args.body_composition = True
            args.stats_history = True
            # Set no limit on activity details
            args.activity_limit = 0
        
        # Retrieve detailed activity data if requested
        if args.detailed_activities:
            try:
                if 'activities' in data and not data['activities'].empty:
                    logger.info("Retrieving detailed activity data...")
                    
                    # Determine limit for activities
                    limit = None
                    if hasattr(args, 'activity_limit') and args.activity_limit is not None:
                        if args.activity_limit > 0:
                            limit = args.activity_limit
                            logger.info(f"Limiting detailed activity retrieval to {limit} activities")
                        else:
                            logger.info("Retrieving ALL detailed activities (no limit)")
                    else:
                        # Default limit if not specified
                        limit = 100
                        logger.info(f"Using default limit of {limit} activities for detailed data")
                        
                    activity_details = connector.get_activity_details_for_all(
                        activities_df=data['activities'], limit=limit
                    )
                    if activity_details:
                        data['activity_details'] = activity_details
                        logger.info(f"  - {len(activity_details)} detailed activity data retrieved")
            except Exception as e:
                logger.error(f"Error retrieving detailed activity data: {e}")
        
        # Retrieve health data if requested
        if args.health_data:
            logger.info("Retrieving health data...")
            
            # Weight data
            try:
                weight_data = connector.get_weight_data(start_date=start_date, end_date=end_date)
                if not weight_data.empty:
                    data['weight_data'] = weight_data
                    logger.info(f"  - {len(weight_data)} weight data records retrieved")
            except Exception as e:
                logger.error(f"Error retrieving weight data: {e}")
            
            # Heart rate data
            try:
                heart_rate_data = connector.get_heart_rates(
                    start_date=max(start_date, (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")),
                    end_date=end_date
                )
                if not heart_rate_data.empty:
                    data['heart_rate_data'] = heart_rate_data
                    logger.info(f"  - {len(heart_rate_data)} heart rate data records retrieved")
            except Exception as e:
                logger.error(f"Error retrieving heart rate data: {e}")
            
            # Sleep data
            try:
                sleep_data = connector.get_sleep_data(
                    start_date=max(start_date, (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")),
                    end_date=end_date
                )
                if not sleep_data.empty:
                    data['sleep_data'] = sleep_data
                    logger.info(f"  - {len(sleep_data)} sleep data records retrieved")
            except Exception as e:
                logger.error(f"Error retrieving sleep data: {e}")
            
            # Stress data
            try:
                stress_data = connector.get_stress_data(
                    start_date=max(start_date, (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")),
                    end_date=end_date
                )
                if not stress_data.empty:
                    data['stress_data'] = stress_data
                    logger.info(f"  - {len(stress_data)} stress data records retrieved")
            except Exception as e:
                logger.error(f"Error retrieving stress data: {e}")
            
            # Metrics (VO2Max, etc.)
            try:
                metrics_data = connector.get_metrics_data(start_date=start_date, end_date=end_date)
                if metrics_data:
                    data['metrics_data'] = metrics_data
                    logger.info("  - Training metrics retrieved")
            except Exception as e:
                logger.error(f"Error retrieving training metrics: {e}")
        
        # Detailed body composition if requested
        if args.body_composition:
            try:
                logger.info("Retrieving detailed body composition data...")
                body_composition = connector.get_body_composition_detailed(
                    start_date=start_date, end_date=end_date
                )
                if not body_composition.empty:
                    data['body_composition'] = body_composition
                    logger.info(f"  - {len(body_composition)} body composition records retrieved")
            except Exception as e:
                logger.error(f"Error retrieving detailed body composition data: {e}")
        
        # Long-term statistics if requested
        if args.stats_history:
            try:
                logger.info("Retrieving long-term statistics...")
                user_stats = connector.get_user_stats_history()
                if user_stats:
                    data['user_stats'] = user_stats
                    logger.info("  - Long-term statistics retrieved")
            except Exception as e:
                logger.error(f"Error retrieving long-term statistics: {e}")
        
        return data
    
    except Exception as e:
        logger.error(f"Error connecting to Garmin Connect: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {}

def main():
    args = parse_args()
    
    # Check if we're using Garmin Connect API or files
    if GARMIN_CONNECT_AVAILABLE and args.connect:
        # Get data from Garmin Connect API
        logger.info("Using Garmin Connect API for data retrieval")
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
        # Convert Dictionary to DataFrame if needed
        if isinstance(df, dict):
            df = pd.DataFrame([df])
        
        if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
            repository.save_data(data_type, df)
            logger.info(f"Saved {len(df)} records to {data_type}")
    
    # Print summary of loaded data
    print("\n=== Garmin Fitness Assistant ===")
    for data_type, df in data.items():
        # Convert Dictionary to DataFrame if needed
        if isinstance(df, dict):
            df = pd.DataFrame([df])
        
        if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
            print(f"\n{data_type.replace('_', ' ').title()}:")
            print(f"  - {len(df)} records")
            
            # Try to display date range
            if 'timestamp' in df.columns:
                try:
                    # Try to convert to datetime if it's a string
                    if pd.api.types.is_string_dtype(df['timestamp']):
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
                    print(f"  - Date range: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")
                except Exception as e:
                    # Try the special case for heart rate data
                    if data_type == 'heart_rate_data' and 'timestamp' in df.columns and 'value' in df.columns:
                        # For heart rate data with [timestamp, value] format
                        if pd.api.types.is_integer_dtype(df['timestamp']):
                            # For int64 timestamps (UNIX timestamps)
                            try:
                                earliest = pd.to_datetime(df['timestamp'].min(), unit='ms')
                                latest = pd.to_datetime(df['timestamp'].max(), unit='ms')
                                print(f"  - Date range: {earliest.date()} to {latest.date()}")
                            except Exception as e:
                                print(f"  - Date range: Special format - could not convert")
                    else:
                        print(f"  - Date range: Unable to format timestamps - {e}")
            elif 'date' in df.columns:
                try:
                    # Try to convert to datetime if it's a string
                    if pd.api.types.is_string_dtype(df['date']):
                        df['date'] = pd.to_datetime(df['date'])
                    
                    print(f"  - Date range: {df['date'].min().date()} to {df['date'].max().date()}")
                except Exception as e:
                    print(f"  - Date range: Unable to format dates - {e}")
    
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
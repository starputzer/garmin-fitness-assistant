import os
import sys
import argparse
from pathlib import Path
import pandas as pd

# Ensure the project root is in the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.backend.parsers.garmin_parser import GarminParser
from src.backend.analysis.run_analyzer import RunAnalyzer
from src.backend.common.data_repository import GarminDataRepository


def parse_args():
    parser = argparse.ArgumentParser(description='Garmin Fitness Assistant')
    parser.add_argument('--data-dir', type=str, help='Directory containing Garmin export files')
    parser.add_argument('--storage-dir', type=str, default='./data/storage', help='Directory for storing processed data')
    parser.add_argument('--predictions-file', type=str, help='Path to race predictions JSON file')
    parser.add_argument('--training-file', type=str, help='Path to training history JSON file')
    parser.add_argument('--metrics-file', type=str, help='Path to metrics JSON file')
    parser.add_argument('--activities-file', type=str, help='Path to activities JSON file')
    parser.add_argument('--analyze', action='store_true', help='Perform analysis after parsing')
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Check if data directory or individual files are provided
    if not args.data_dir and not (args.predictions_file or args.training_file or args.metrics_file or args.activities_file):
        print("Error: Either --data-dir or specific file paths must be provided.")
        return 1
    
    # Initialize parser
    parser = GarminParser(data_dir=args.data_dir)
    
    # Initialize data repository
    repository = GarminDataRepository(storage_path=args.storage_dir)
    
    # Parse available data
    data = {}
    
    try:
        if args.predictions_file:
            data['race_predictions'] = parser.parse_race_predictions(args.predictions_file)
        elif args.data_dir:
            try:
                data['race_predictions'] = parser.parse_race_predictions()
            except FileNotFoundError:
                print("Race predictions file not found.")
        
        if args.training_file:
            data['training_history'] = parser.parse_training_history(args.training_file)
        elif args.data_dir:
            try:
                data['training_history'] = parser.parse_training_history()
            except FileNotFoundError:
                print("Training history file not found.")
        
        if args.metrics_file:
            data['heat_altitude_metrics'] = parser.parse_heat_altitude_metrics(args.metrics_file)
        elif args.data_dir:
            try:
                data['heat_altitude_metrics'] = parser.parse_heat_altitude_metrics()
            except FileNotFoundError:
                print("Heat/altitude metrics file not found.")
        
        if args.activities_file:
            data['activities'] = parser.parse_activities(args.activities_file)
        elif args.data_dir:
            try:
                data['activities'] = parser.parse_activities()
            except FileNotFoundError:
                print("Activities file not found.")
    except Exception as e:
        print(f"Error parsing data: {e}")
        return 1
    
    # Save parsed data to repository
    for data_type, df in data.items():
        if df is not None:
            repository.save_data(data_type, df)
    
    # Print summary of loaded data
    print("\n=== Garmin Fitness Assistant ===")
    for data_type, df in data.items():
        if df is not None:
            print(f"\n{data_type.replace('_', ' ').title()}:")
            print(f"  - {len(df)} records")
            if 'timestamp' in df.columns:
                print(f"  - Date range: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")
    
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
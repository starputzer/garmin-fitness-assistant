from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import uvicorn
import json
import tempfile
import os
import sys
from pathlib import Path
import shutil
from datetime import datetime, timedelta
import pandas as pd

from src.backend.parsers.garmin_parser import GarminParser
from src.backend.analysis.run_analyzer import RunAnalyzer
from src.backend.llm.training_advisor import LLMTrainingAdvisor
from src.backend.common.data_repository import GarminDataRepository

project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

class WebAPI:
    def __init__(self, host, port, parser, analyzer, advisor, repository):
        """
        Initialize the Web API with necessary components.
        
        Args:
            host (str): Host address to bind the server to.
            port (int): Port number to listen on.
            parser (GarminParser): Instance of GarminParser for data parsing.
            analyzer (RunAnalyzer): Instance of RunAnalyzer for data analysis.
            advisor (LLMTrainingAdvisor): Instance of LLMTrainingAdvisor for recommendations.
            repository (GarminDataRepository): Instance of GarminDataRepository for data storage.
        """
        self.host = host
        self.port = port
        self.parser = parser
        self.analyzer = analyzer
        self.advisor = advisor
        self.repository = repository
        
        # Initialize FastAPI app
        self.app = FastAPI(title="Garmin Fitness Assistant API")
        
        # Add CORS middleware to allow cross-origin requests
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins
            allow_credentials=True,
            allow_methods=["*"],  # Allow all methods
            allow_headers=["*"],  # Allow all headers
        )
        
        # Configure routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up API routes."""
        
        @self.app.get("/")
        async def root():
            return {"message": "Welcome to Garmin Fitness Assistant API"}
        
        @self.app.post("/upload/")
        async def upload_files(
            background_tasks: BackgroundTasks,
            files: List[UploadFile] = File(...),
            user_id: Optional[str] = Form("default")
        ):
            """
            Upload Garmin data files for processing.
            
            Args:
                files: List of files to upload
                user_id: Optional user ID for multi-user support
            """
            # Create a temporary directory to store the uploaded files
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Save the uploaded files to the temporary directory
                for file in files:
                    file_path = os.path.join(temp_dir, file.filename)
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                
                # Use parser to process the files in the background
                background_tasks.add_task(self._process_files, temp_dir, user_id)
                
                return JSONResponse(
                    status_code=202,
                    content={
                        "message": "Files uploaded successfully. Processing in background.",
                        "files": [file.filename for file in files]
                    }
                )
            except Exception as e:
                shutil.rmtree(temp_dir)  # Clean up the temporary directory
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/analyze/race_times/")
        async def analyze_race_times(
            distance: str = "5K",
            days: int = 90,
            user_id: Optional[str] = "default"
        ):
            """
            Analyze race time predictions.
            
            Args:
                distance: Race distance ('5K', '10K', 'Half', 'Marathon')
                days: Number of days to analyze
                user_id: User ID for multi-user support
            """
            try:
                # Load the most recent race predictions data
                race_predictions_data = self.repository.load_data('race_predictions', user_id)
                
                if not race_predictions_data:
                    raise HTTPException(status_code=404, detail="No race predictions data found")
                
                # Convert to DataFrame
                race_df = pd.DataFrame(race_predictions_data)
                
                # Ensure timestamp is datetime
                race_df['timestamp'] = pd.to_datetime(race_df['timestamp'])
                
                # Set data in analyzer
                self.analyzer.set_race_predictions(race_df)
                
                # Get latest predictions
                latest_predictions = self.analyzer.get_latest_predictions()
                
                # Calculate improvement
                cutoff_date = datetime.now() - timedelta(days=days)
                improvement = self.analyzer.calculate_improvement(
                    distance=distance,
                    start_date=cutoff_date,
                    end_date=datetime.now()
                )
                
                # Generate plot data (simplified for JSON response)
                cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
                filtered_df = race_df[race_df['timestamp'] > cutoff_date].copy()
                
                # Determine the column to use based on the distance
                if distance == '5K':
                    time_col = 'raceTime5K'
                elif distance == '10K':
                    time_col = 'raceTime10K'
                elif distance == 'Half':
                    time_col = 'raceTimeHalf'
                elif distance == 'Marathon':
                    time_col = 'raceTimeMarathon'
                else:
                    raise HTTPException(status_code=400, detail=f"Invalid distance: {distance}")
                
                # Sort and prepare plot data
                filtered_df = filtered_df.sort_values('timestamp')
                plot_data = {
                    'dates': filtered_df['timestamp'].dt.strftime('%Y-%m-%d').tolist(),
                    'times': filtered_df[time_col].tolist()
                }
                
                return {
                    "latest_predictions": latest_predictions,
                    "improvement": improvement,
                    "plot_data": plot_data
                }
            except HTTPException as e:
                raise e
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/analyze/training_status/")
        async def analyze_training_status(
            days: int = 90,
            user_id: Optional[str] = "default"
        ):
            """
            Analyze training status.
            
            Args:
                days: Number of days to analyze
                user_id: User ID for multi-user support
            """
            try:
                # Load the most recent training history data
                training_data = self.repository.load_data('training_history', user_id)
                
                if not training_data:
                    raise HTTPException(status_code=404, detail="No training history data found")
                
                # Convert to DataFrame
                training_df = pd.DataFrame(training_data)
                
                # Ensure timestamp is datetime
                training_df['timestamp'] = pd.to_datetime(training_df['timestamp'])
                training_df['calendarDate'] = pd.to_datetime(training_df['calendarDate'])
                
                # Set data in analyzer
                self.analyzer.set_training_history(training_df)
                
                # Analyze training status
                status_analysis = self.analyzer.analyze_training_status(days=days)
                
                # Convert figure to data for JSON response
                # We'll simplify this to just status counts and daily status
                cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
                filtered_df = training_df[training_df['timestamp'] > cutoff_date].copy()
                
                # Prepare daily training status
                daily_status = filtered_df.groupby(filtered_df['calendarDate'].dt.date)['trainingStatus'].agg(lambda x: x.mode()[0] if not x.empty else None)
                daily_status = {str(date): status for date, status in daily_status.items()}
                
                return {
                    "status_counts": status_analysis['status_counts'],
                    "daily_status": daily_status
                }
            except HTTPException as e:
                raise e
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/recommendations/")
        async def get_recommendations(
            user_id: Optional[str] = "default"
        ):
            """
            Get training recommendations.
            
            Args:
                user_id: User ID for multi-user support
            """
            try:
                # Load data for the advisor
                race_data = self.repository.load_data('race_predictions', user_id)
                training_data = self.repository.load_data('training_history', user_id)
                activities_data = self.repository.load_data('activities', user_id)
                
                if not race_data and not training_data:
                    raise HTTPException(status_code=404, detail="Insufficient data for recommendations")
                
                # Convert to DataFrames
                race_df = pd.DataFrame(race_data) if race_data else None
                training_df = pd.DataFrame(training_data) if training_data else None
                activities_df = pd.DataFrame(activities_data) if activities_data else None
                
                # Set data in the advisor
                self.advisor.set_data(race_df, training_df, activities_df)
                
                # Generate recommendations
                workout_suggestions = self.advisor.suggest_workouts(count=3)
                recovery_recommendations = self.advisor.evaluate_recovery_needs()
                progress_analysis = self.advisor.analyze_progress(previous_weeks=4)
                
                return {
                    "workout_suggestions": workout_suggestions,
                    "recovery_recommendations": recovery_recommendations,
                    "progress_analysis": progress_analysis
                }
            except HTTPException as e:
                raise e
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/training_plan/")
        async def create_training_plan(
            goal_distance: str,
            target_time: str,
            weeks: int = 8,
            sessions_per_week: int = 4,
            user_id: Optional[str] = "default"
        ):
            """
            Create a training plan.
            
            Args:
                goal_distance: Goal race distance ('5K', '10K', 'Half', 'Marathon')
                target_time: Target time in format MM:SS or HH:MM:SS
                weeks: Number of weeks for the plan
                sessions_per_week: Number of sessions per week
                user_id: User ID for multi-user support
            """
            try:
                # Load data for the advisor
                race_data = self.repository.load_data('race_predictions', user_id)
                training_data = self.repository.load_data('training_history', user_id)
                activities_data = self.repository.load_data('activities', user_id)
                
                # Convert to DataFrames
                race_df = pd.DataFrame(race_data) if race_data else None
                training_df = pd.DataFrame(training_data) if training_data else None
                activities_df = pd.DataFrame(activities_data) if activities_data else None
                
                # Set data in the advisor
                self.advisor.set_data(race_df, training_df, activities_df)
                
                # Generate training plan
                training_plan = self.advisor.generate_training_plan(
                    goal_distance=goal_distance,
                    target_time=target_time,
                    weeks=weeks,
                    sessions_per_week=sessions_per_week
                )
                
                return training_plan
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/data/list/")
        async def list_data(
            user_id: Optional[str] = "default"
        ):
            """
            List available data for a user.
            
            Args:
                user_id: User ID for multi-user support
            """
            try:
                available_data = self.repository.list_available_data(user_id)
                return available_data
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _process_files(self, temp_dir, user_id):
        """
        Process uploaded files in the background.
        
        Args:
            temp_dir: Directory containing the uploaded files
            user_id: User ID for multi-user support
        """
        try:
            # Create a new parser instance with the temporary directory
            temp_parser = GarminParser(data_dir=temp_dir)
            
            # Parse all available data
            parsed_data = temp_parser.parse_all_available()
            
            # Save parsed data to repository
            for data_type, df in parsed_data.items():
                if df is not None:
                    self.repository.save_data(data_type, df, user_id=user_id)
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)
    
    def start_server(self):
        """Start the API server."""
        uvicorn.run(self.app, host=self.host, port=self.port)


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Garmin Fitness Assistant API")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--data-dir", type=str, default="./data", help="Data directory")
    parser.add_argument("--storage-dir", type=str, default="./data/storage", help="Storage directory")
    parser.add_argument("--model-name", type=str, default="llama3:8b-instruct-q4_1", help="LLM model name")
    parser.add_argument("--model-endpoint", type=str, default="http://localhost:11434", help="LLM API endpoint")
    
    args = parser.parse_args()
    
    # Initialize components
    garmin_parser = GarminParser(data_dir=args.data_dir)
    run_analyzer = RunAnalyzer()
    llm_advisor = LLMTrainingAdvisor(model_name=args.model_name, model_endpoint=args.model_endpoint)
    data_repository = GarminDataRepository(storage_path=args.storage_dir)
    
    # Initialize and start API
    api = WebAPI(
        host=args.host,
        port=args.port,
        parser=garmin_parser,
        analyzer=run_analyzer,
        advisor=llm_advisor,
        repository=data_repository
    )
    
    api.start_server()
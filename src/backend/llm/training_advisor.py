import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class LLMTrainingAdvisor:
    def __init__(self, model_name, model_endpoint):
        """
        Initialize the training advisor with a model name and endpoint.
        
        Args:
            model_name (str): Name of the LLM model to use.
            model_endpoint (str): URL of the model API endpoint.
        """
        self.model_name = model_name
        self.model_endpoint = model_endpoint
        self.race_predictions = None
        self.training_history = None
        self.activities = None
    
    def set_data(self, race_predictions=None, training_history=None, activities=None):
        """
        Set the data for analysis.
        
        Args:
            race_predictions (pandas.DataFrame, optional): Race predictions data.
            training_history (pandas.DataFrame, optional): Training history data.
            activities (pandas.DataFrame, optional): Activities data.
        """
        self.race_predictions = race_predictions
        self.training_history = training_history
        self.activities = activities
    
    def _prepare_context(self, goal_distance=None, target_time=None):
        """
        Prepare context for the LLM based on available data.
        
        Args:
            goal_distance (str, optional): Goal race distance for training ('5K', '10K', 'Half', 'Marathon').
            target_time (str, optional): Target time for the race in format "MM:SS" or "HH:MM:SS".
            
        Returns:
            str: Context string for the LLM.
        """
        context = []
        
        # Add race predictions context
        if self.race_predictions is not None:
            latest_date = self.race_predictions['timestamp'].max()
            latest_predictions = self.race_predictions[self.race_predictions['timestamp'] == latest_date].iloc[0]
            
            predictions_text = "Current race predictions:\n"
            
            if 'raceTime5K' in latest_predictions:
                time_5k = latest_predictions['raceTime5K']
                predictions_text += f"- 5K: {time_5k // 60}:{time_5k % 60:02d}\n"
            
            if 'raceTime10K' in latest_predictions:
                time_10k = latest_predictions['raceTime10K']
                predictions_text += f"- 10K: {time_10k // 60}:{time_10k % 60:02d}\n"
            
            if 'raceTimeHalf' in latest_predictions:
                time_half = latest_predictions['raceTimeHalf']
                minutes = time_half // 60
                seconds = time_half % 60
                hours = minutes // 60
                minutes = minutes % 60
                predictions_text += f"- Half Marathon: {hours}:{minutes:02d}:{seconds:02d}\n"
            
            if 'raceTimeMarathon' in latest_predictions:
                time_marathon = latest_predictions['raceTimeMarathon']
                minutes = time_marathon // 60
                seconds = time_marathon % 60
                hours = minutes // 60
                minutes = minutes % 60
                predictions_text += f"- Marathon: {hours}:{minutes:02d}:{seconds:02d}\n"
            
            context.append(predictions_text)
        
        # Add training history context
        if self.training_history is not None:
            # Get recent training status
            recent_df = self.training_history.sort_values('timestamp', ascending=False).head(30)
            status_counts = recent_df['trainingStatus'].value_counts()
            
            status_text = "Recent training status (last 30 days):\n"
            for status, count in status_counts.items():
                status_text += f"- {status}: {count} days\n"
            
            context.append(status_text)
        
        # Add activities context
        if self.activities is not None:
            # This part would need to be customized based on actual structure of activities data
            context.append("Recent activities data is available.")
        
        # Add goal context
        if goal_distance is not None:
            context.append(f"Goal race distance: {goal_distance}")
        
        if target_time is not None:
            context.append(f"Target time: {target_time}")
        
        return "\n\n".join(context)
    
    def generate_training_plan(self, goal_distance, target_time, weeks=8, sessions_per_week=4):
        """
        Generate a training plan based on the user's data and goals.
        
        Args:
            goal_distance (str): Goal race distance ('5K', '10K', 'Half', 'Marathon').
            target_time (str): Target time for the race in format "MM:SS" or "HH:MM:SS".
            weeks (int, optional): Number of weeks for the training plan.
            sessions_per_week (int, optional): Number of sessions per week.
            
        Returns:
            dict: Training plan with weekly structure.
        """
        # Prepare context
        context = self._prepare_context(goal_distance, target_time)
        
        # Prepare prompt
        prompt = f"""
        {context}
        
        Create a {weeks}-week training plan for a {goal_distance} race with a target time of {target_time}.
        The plan should include {sessions_per_week} sessions per week.
        For each session, provide:
        1. Day of the week
        2. Type of session (e.g., Easy Run, Interval, Tempo, Long Run)
        3. Distance or duration
        4. Target pace or intensity
        5. Description of the workout
        
        The plan should progressively build up and include appropriate tapering before the race.
        """
        
        # Call LLM API (simplified for now)
        try:
            response = self._call_llm_api(prompt)
            
            # Parse and structure the response
            # This will depend on the actual response format from the LLM
            plan = self._parse_training_plan(response, weeks, sessions_per_week)
            
            return plan
        except Exception as e:
            print(f"Error generating training plan: {e}")
            return {"error": str(e)}
    
    def analyze_progress(self, previous_weeks=4):
        """
        Analyze progress over the past few weeks.
        
        Args:
            previous_weeks (int, optional): Number of weeks to analyze.
            
        Returns:
            dict: Progress analysis.
        """
        # Prepare context
        context = self._prepare_context()
        
        # Prepare prompt
        prompt = f"""
        {context}
        
        Analyze the progress over the past {previous_weeks} weeks. Consider:
        1. Changes in predicted race times
        2. Training status changes
        3. Training load and recovery patterns
        
        Provide insights on:
        - Whether training is effective
        - Areas of improvement
        - Potential risks or issues
        """
        
        # Call LLM API
        try:
            response = self._call_llm_api(prompt)
            
            # For now, return raw response
            return {"analysis": response}
        except Exception as e:
            print(f"Error analyzing progress: {e}")
            return {"error": str(e)}
    
    def suggest_workouts(self, count=3):
        """
        Suggest workouts based on the user's current fitness and goals.
        
        Args:
            count (int, optional): Number of workouts to suggest.
            
        Returns:
            list: Suggested workouts.
        """
        # Prepare context
        context = self._prepare_context()
        
        # Prepare prompt
        prompt = f"""
        {context}
        
        Suggest {count} workouts that would be beneficial based on the current fitness level and training status.
        For each workout, provide:
        1. Workout type
        2. Duration or distance
        3. Target intensity
        4. Detailed description
        5. Expected benefits
        """
        
        # Call LLM API
        try:
            response = self._call_llm_api(prompt)
            
            # Parse and structure the response
            workouts = self._parse_workouts(response, count)
            
            return workouts
        except Exception as e:
            print(f"Error suggesting workouts: {e}")
            return [{"error": str(e)}]
    
    def evaluate_recovery_needs(self):
        """
        Evaluate recovery needs based on recent training.
        
        Returns:
            dict: Recovery recommendations.
        """
        # Prepare context
        context = self._prepare_context()
        
        # Prepare prompt
        prompt = f"""
        {context}
        
        Evaluate the current recovery needs based on recent training.
        Consider:
        1. Training load
        2. Training status
        3. Recent workout intensity
        
        Provide recommendations on:
        - Recovery techniques
        - Rest days needed
        - Warning signs to watch for
        """
        
        # Call LLM API
        try:
            response = self._call_llm_api(prompt)
            
            # For now, return raw response
            return {"recovery_recommendations": response}
        except Exception as e:
            print(f"Error evaluating recovery needs: {e}")
            return {"error": str(e)}
    
    def _call_llm_api(self, prompt):
        """
        Call the LLM API with a prompt.
        
        Args:
            prompt (str): Prompt for the LLM.
            
        Returns:
            str: Response from the LLM.
        """
        # This is a placeholder implementation
        # The actual implementation would depend on the specific LLM API being used
        
        # For local OLLAMA
        if "ollama" in self.model_endpoint:
            try:
                data = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
                response = requests.post(f"{self.model_endpoint}/api/generate", json=data)
                response.raise_for_status()
                return response.json().get("response", "")
            except Exception as e:
                print(f"Error calling OLLAMA API: {e}")
                # For development/testing, return a placeholder response
                return "This is a placeholder response for development purposes."
        else:
            # Generic API handler, would need to be adapted for specific APIs
            return "LLM API not implemented for this endpoint."
    
    def _parse_training_plan(self, response, weeks, sessions_per_week):
        """
        Parse the LLM response into a structured training plan.
        
        Args:
            response (str): Raw response from the LLM.
            weeks (int): Number of weeks in the plan.
            sessions_per_week (int): Number of sessions per week.
            
        Returns:
            dict: Structured training plan.
        """
        # This is a very simplified parser
        # Actual implementation would need to be adapted based on the LLM response format
        
        # For now, just structure the raw response
        plan = {
            "weeks": weeks,
            "sessions_per_week": sessions_per_week,
            "raw_plan": response,
            "structured_plan": {}
        }
        
        # Attempt to structure the plan (basic version)
        for week in range(1, weeks + 1):
            plan["structured_plan"][f"Week {week}"] = []
        
        return plan
    
    def _parse_workouts(self, response, count):
        """
        Parse the LLM response into structured workout suggestions.
        
        Args:
            response (str): Raw response from the LLM.
            count (int): Expected number of workouts.
            
        Returns:
            list: Structured workout suggestions.
        """
        # This is a very simplified parser
        # Actual implementation would need to be adapted based on the LLM response format
        
        # For now, just return a list with the raw response
        return [{"raw_suggestion": response}]
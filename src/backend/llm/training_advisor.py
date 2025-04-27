import requests
import json
import pandas as pd
import numpy as np
import platform
import os
from datetime import datetime, timedelta


class LLMTrainingAdvisor:
    def __init__(self, model_name, model_endpoint):
        """
        Initialize the training advisor with a model name and endpoint.
        
        Args:
            model_name (str): Name of the LLM model to use.
            model_endpoint (str): URL of the model API endpoint.
        """
        # Überprüfen, ob wir im Mock-Modus laufen sollen
        self.use_mock = platform.system() == "Windows" or os.environ.get("USE_MOCK_LLM", "0") == "1"
        
        if self.use_mock:
            print(f"INFO: Verwende Mock-LLM-Implementierung (Mock-Modus: {platform.system()})")
            self.model_name = "mock-model"
            self.model_endpoint = "mock-endpoint"
        else:
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
        Call the LLM API with a prompt, or provide mock responses on Windows.
        
        Args:
            prompt (str): Prompt for the LLM.
            
        Returns:
            str: Response from the LLM or mock response.
        """
        # Mock-Modus: Generiere plausible Antworten ohne externe API
        if self.use_mock:
            # Extrahiere Schlüsselwörter aus dem Prompt für angepasste Mock-Antworten
            keywords = {
                "training plan": self._generate_mock_training_plan(prompt),
                "workouts": self._generate_mock_workouts(prompt),
                "progress": self._generate_mock_progress_analysis(prompt),
                "recovery": self._generate_mock_recovery_recommendation(prompt)
            }
            
            # Wähle die passende Mock-Antwort basierend auf Schlüsselwörtern im Prompt
            for key, response in keywords.items():
                if key in prompt.lower():
                    return response
            
            # Generische Antwort, wenn keine spezifischen Schlüsselwörter gefunden wurden
            return "This is a generic mock response for development purposes."
        
        # Echter API-Aufruf für Produktionsumgebungen
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
                # Auch im Produktionsmodus einen Fallback anbieten
                return "LLM API error - please check your connection and try again."
        else:
            # Generic API handler, would need to be adapted for specific APIs
            return "LLM API not implemented for this endpoint."
    
    def _generate_mock_training_plan(self, prompt):
        """Generate a realistic mock training plan"""
        # Extrahiere Informationen aus dem Prompt
        goal_info = ""
        if "5K" in prompt:
            goal_info = "5K race"
        elif "10K" in prompt:
            goal_info = "10K race"
        elif "Half" in prompt:
            goal_info = "Half Marathon"
        elif "Marathon" in prompt:
            goal_info = "Marathon"
        
        return f"""# 8-Week Training Plan for {goal_info}

## Week 1: Foundation
- Monday: Rest day
- Tuesday: Easy run, 30 minutes at conversational pace
- Wednesday: Rest or cross-training
- Thursday: Interval training, 5x400m with 200m recovery jogs
- Saturday: Long run, 45 minutes at easy pace

## Week 2: Building
- Monday: Rest day
- Tuesday: Easy run, 35 minutes at conversational pace
- Wednesday: Rest or cross-training
- Thursday: Tempo run, 20 minutes at comfortably hard pace
- Saturday: Long run, 50 minutes at easy pace

## Week 3-8: [Additional structured training content]

This training plan progressively builds endurance and speed while including adequate recovery periods. Adjust based on your current fitness level and how you're feeling.
"""
    
    def _generate_mock_workouts(self, prompt):
        """Generate mock workout suggestions"""
        return """Here are three workout suggestions based on your current fitness level:

1. **Fartlek Workout**
   - Duration: 40 minutes
   - Intensity: Varied
   - Description: After a 10-minute warm-up, alternate between 2 minutes at tempo pace and 1 minute easy recovery. Repeat 8 times, then cool down for 10 minutes.
   - Benefits: Improves lactate threshold and mental toughness

2. **Hill Repeats**
   - Duration: 45 minutes
   - Intensity: High
   - Description: Find a moderate hill (4-6% grade) that takes about 30-60 seconds to climb. After a 10-minute warm-up, run hard uphill, then jog or walk back down. Repeat 8-10 times.
   - Benefits: Builds power, strength, and running economy

3. **Progressive Long Run**
   - Duration: 75 minutes
   - Intensity: Easy to moderate
   - Description: Start at an easy pace for 45 minutes, then gradually increase pace for the final 30 minutes, finishing at your half marathon pace.
   - Benefits: Teaches your body to perform while fatigued, improves endurance
"""
    
    def _generate_mock_progress_analysis(self, prompt):
        """Generate a mock progress analysis"""
        return """## Progress Analysis (Last 4 Weeks)

Your training data shows consistent improvement over the past month:

### Strengths:
- Your 5K predicted time has improved by approximately 2.5%
- Training consistency has been excellent with 85% adherence to planned workouts
- Aerobic endurance shows significant gains based on long run performance

### Areas for Improvement:
- Recovery patterns indicate potential insufficient rest between hard sessions
- Speed work appears to be less consistent than endurance training
- Consider adding more variety in workout types

### Recommendations:
1. Continue the current volume but ensure at least two complete rest days per week
2. Incorporate more structured interval sessions to improve speed
3. Consider adding strength training twice weekly to prevent injury and improve running economy

Overall, your training trajectory is positive with good adaptations occurring. Minor adjustments to recovery and workout variety should lead to continued improvement.
"""
    
    def _generate_mock_recovery_recommendation(self, prompt):
        """Generate mock recovery recommendations"""
        return """## Recovery Recommendations

Based on your recent training patterns, here are personalized recovery recommendations:

### Current Status Assessment:
- Training load has been moderately high over the past 10 days
- Recent high-intensity sessions may require additional recovery
- Some early warning signs of potential fatigue are present

### Recovery Recommendations:
1. **Immediate Actions:**
   - Schedule 1-2 complete rest days this week
   - Reduce intensity for the next 3-4 days
   - Focus on sleep quality (aim for 7-9 hours)

2. **Recovery Techniques:**
   - Implement 10-15 minutes of daily foam rolling
   - Consider contrast therapy (alternating hot and cold)
   - Gentle yoga or stretching on rest days

3. **Nutrition Focus:**
   - Increase protein intake slightly (1.6-1.8g/kg body weight)
   - Ensure adequate carbohydrate replenishment after workouts
   - Consider tart cherry juice to reduce inflammation

### Warning Signs to Monitor:
- Resting heart rate elevated by more than 7 bpm
- Persistent muscle soreness lasting >72 hours
- Declining performance despite feeling high effort

Implement these recovery strategies to maintain training consistency and prevent overtraining.
"""
    
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
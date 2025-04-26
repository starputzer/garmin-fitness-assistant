import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go


class RunAnalyzer:
    def __init__(self, race_predictions_df=None, training_history_df=None):
        """
        Initialize the analyzer with race predictions and training history data.
        
        Args:
            race_predictions_df (pandas.DataFrame, optional): DataFrame of race predictions.
            training_history_df (pandas.DataFrame, optional): DataFrame of training history.
        """
        self.race_predictions = race_predictions_df
        self.training_history = training_history_df
    
    def set_race_predictions(self, df):
        """Set the race predictions DataFrame."""
        self.race_predictions = df
    
    def set_training_history(self, df):
        """Set the training history DataFrame."""
        self.training_history = df
    
    def get_latest_predictions(self):
        """
        Get the most recent race predictions.
        
        Returns:
            dict: Dictionary of latest predictions for each race distance.
        """
        if self.race_predictions is None:
            raise ValueError("Race predictions data not loaded.")
        
        latest_date = self.race_predictions['timestamp'].max()
        latest_row = self.race_predictions[self.race_predictions['timestamp'] == latest_date].iloc[0]
        
        return {
            '5K': latest_row.get('raceTime5K_formatted', latest_row.get('raceTime5K')),
            '10K': latest_row.get('raceTime10K_formatted', latest_row.get('raceTime10K')),
            'Half Marathon': latest_row.get('raceTimeHalf_formatted', latest_row.get('raceTimeHalf')),
            'Marathon': latest_row.get('raceTimeMarathon_formatted', latest_row.get('raceTimeMarathon'))
        }
    
    def plot_race_time_trends(self, distance='5K', days=90):
        """
        Plot trends in predicted race times for a specific distance.
        
        Args:
            distance (str): Race distance to plot ('5K', '10K', 'Half', 'Marathon').
            days (int): Number of days of history to plot.
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object.
        """
        if self.race_predictions is None:
            raise ValueError("Race predictions data not loaded.")
        
        # Determine the column to use based on the distance
        if distance == '5K':
            time_col = 'raceTime5K'
            title = '5K Race Time Predictions'
            y_label = '5K Time (seconds)'
        elif distance == '10K':
            time_col = 'raceTime10K'
            title = '10K Race Time Predictions'
            y_label = '10K Time (seconds)'
        elif distance == 'Half':
            time_col = 'raceTimeHalf'
            title = 'Half Marathon Race Time Predictions'
            y_label = 'Half Marathon Time (seconds)'
        elif distance == 'Marathon':
            time_col = 'raceTimeMarathon'
            title = 'Marathon Race Time Predictions'
            y_label = 'Marathon Time (seconds)'
        else:
            raise ValueError(f"Invalid distance: {distance}")
        
        # Filter data for the specified number of days
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
        filtered_df = self.race_predictions[self.race_predictions['timestamp'] > cutoff_date].copy()
        
        # Sort by timestamp
        filtered_df = filtered_df.sort_values('timestamp')
        
        # Create a figure using Plotly
        fig = px.line(
            filtered_df, 
            x='timestamp', 
            y=time_col,
            title=title
        )
        
        # Add formatted times as hover text
        formatted_col = f'{time_col}_formatted'
        if formatted_col in filtered_df.columns:
            hovertemplate = '%{x}<br>Time: %{customdata}'
            fig.update_traces(
                customdata=filtered_df[formatted_col],
                hovertemplate=hovertemplate
            )
        
        # Improve layout
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title=y_label,
            hovermode='closest'
        )
        
        # For better visualization, invert the y-axis (lower time is better)
        fig.update_yaxes(autorange="reversed")
        
        return fig
    
    def analyze_training_status(self, days=90):
        """
        Analyze training status over time.
        
        Args:
            days (int): Number of days of history to analyze.
            
        Returns:
            dict: Dictionary with analysis results.
            plotly.graph_objects.Figure: Plotly figure visualizing training status.
        """
        if self.training_history is None:
            raise ValueError("Training history data not loaded.")
        
        # Filter data for the specified number of days
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
        filtered_df = self.training_history[self.training_history['timestamp'] > cutoff_date].copy()
        
        # Count occurrences of each training status
        status_counts = filtered_df['trainingStatus'].value_counts().to_dict()
        
        # Analyze trends (simplified)
        status_by_date = filtered_df.groupby(filtered_df['timestamp'].dt.date)['trainingStatus'].agg(pd.Series.mode)
        
        # Create visualization
        fig = px.bar(
            filtered_df.groupby(['calendarDate', 'trainingStatus']).size().reset_index(name='count'),
            x='calendarDate',
            y='count',
            color='trainingStatus',
            title='Training Status Over Time'
        )
        
        return {
            'status_counts': status_counts,
            'status_by_date': status_by_date.to_dict(),
            'figure': fig
        }
    
    def calculate_improvement(self, distance='5K', start_date=None, end_date=None):
        """
        Calculate improvement in race predictions over a time period.
        
        Args:
            distance (str): Race distance to analyze ('5K', '10K', 'Half', 'Marathon').
            start_date (str or datetime, optional): Start date for calculation.
            end_date (str or datetime, optional): End date for calculation.
            
        Returns:
            dict: Dictionary with improvement metrics.
        """
        if self.race_predictions is None:
            raise ValueError("Race predictions data not loaded.")
        
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
            raise ValueError(f"Invalid distance: {distance}")
        
        # Set default dates if not provided
        if start_date is None:
            start_date = self.race_predictions['timestamp'].min()
        if end_date is None:
            end_date = self.race_predictions['timestamp'].max()
        
        # Convert string dates to datetime if necessary
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
        
        # Filter data for the date range
        date_filtered = self.race_predictions[
            (self.race_predictions['timestamp'] >= start_date) &
            (self.race_predictions['timestamp'] <= end_date)
        ].copy()
        
        if len(date_filtered) < 2:
            return {
                'insufficient_data': True,
                'message': 'Insufficient data for the selected date range.'
            }
        
        # Get start and end values
        start_value = date_filtered.loc[date_filtered['timestamp'].idxmin(), time_col]
        end_value = date_filtered.loc[date_filtered['timestamp'].idxmax(), time_col]
        
        # Calculate improvement
        time_diff = start_value - end_value  # Time decreased means improvement
        percent_improvement = (time_diff / start_value) * 100
        
        # Format times for display
        start_time_str = f"{start_value // 60}:{start_value % 60:02d}"
        end_time_str = f"{end_value // 60}:{end_value % 60:02d}"
        time_diff_str = f"{time_diff // 60}:{abs(time_diff) % 60:02d}"
        
        return {
            'distance': distance,
            'start_date': start_date,
            'end_date': end_date,
            'start_time': start_time_str,
            'end_time': end_time_str,
            'time_difference': time_diff_str,
            'time_diff_seconds': time_diff,
            'percent_improvement': percent_improvement,
            'improved': time_diff > 0
        }
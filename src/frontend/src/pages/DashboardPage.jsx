// src/frontend/pages/DashboardPage.jsx
import React, { useState, useEffect } from 'react';
import { useData } from '../context/DataContext';
import { useUser } from '../context/UserContext';
import ActivitySummary from '../components/dashboard/ActivitySummary';
import RacePredictions from '../components/dashboard/RacePredictions';
import TrainingStatus from '../components/dashboard/TrainingStatus';
import { analyzeRaceTimes, analyzeTrainingStatus } from '../services/analysis.service';
import { getRecommendations } from '../services/training.service';
import './DashboardPage.css';

function DashboardPage() {
  const { user } = useUser();
  const { availableData, isLoading: dataLoading } = useData();
  
  const [racePredictions, setRacePredictions] = useState(null);
  const [trainingStatus, setTrainingStatus] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        
        // Check if we have required data
        if (!availableData || !availableData.race_predictions || !availableData.training_history) {
          setError('Keine Daten verfügbar. Bitte laden Sie zuerst Ihre Garmin-Daten hoch.');
          return;
        }
        
        // Fetch race predictions analysis
        const raceData = await analyzeRaceTimes('5K', 30, user?.id);
        setRacePredictions(raceData);
        
        // Fetch training status analysis
        const statusData = await analyzeTrainingStatus(30, user?.id);
        setTrainingStatus(statusData);
        
        // Fetch quick recommendations
        const recsData = await getRecommendations(user?.id);
        setRecommendations(recsData);
        
        setError(null);
      } catch (err) {
        console.error('Dashboard Ladefehler:', err);
        setError('Fehler beim Laden der Dashboard-Daten: ' + err.message);
      } finally {
        setIsLoading(false);
      }
    };

    if (!dataLoading && availableData) {
      fetchDashboardData();
    }
  }, [availableData, dataLoading, user]);

  // Render loading state
  if (dataLoading || isLoading) {
    return <div className="loading-container">Daten werden geladen...</div>;
  }

  // Render error state
  if (error) {
    return (
      <div className="error-container">
        <h2>Fehler</h2>
        <p>{error}</p>
        <p>Bitte gehen Sie zur <a href="/upload">Upload-Seite</a>, um Ihre Garmin-Daten hochzuladen.</p>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <h1>Fitness Dashboard</h1>
      
      <div className="dashboard-grid">
        <div className="dashboard-item race-predictions">
          <h2>Aktuelle Rennprognosen</h2>
          {racePredictions?.latest_predictions ? (
            <RacePredictions predictions={racePredictions.latest_predictions} />
          ) : (
            <p>Keine Rennprognosen verfügbar</p>
          )}
        </div>
        
        <div className="dashboard-item training-status">
          <h2>Trainingsstatus</h2>
          {trainingStatus ? (
            <TrainingStatus statusData={trainingStatus} />
          ) : (
            <p>Kein Trainingsstatus verfügbar</p>
          )}
        </div>
        
        <div className="dashboard-item recommended-workout">
          <h2>Empfohlenes Training</h2>
          {recommendations?.workout_suggestions?.[0] ? (
            <div className="workout-suggestion">
              <h3>{recommendations.workout_suggestions[0].type || 'Trainingsempfehlung'}</h3>
              <p>{recommendations.workout_suggestions[0].raw_suggestion}</p>
            </div>
          ) : (
            <p>Keine Trainingsempfehlungen verfügbar</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
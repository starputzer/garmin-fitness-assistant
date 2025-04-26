// src/frontend/pages/AnalysisPage.jsx
import React, { useState, useEffect } from 'react';
import { useUser } from '../context/UserContext';
import { useData } from '../context/DataContext';
import RaceTimeChart from '../components/analysis/RaceTimeChart';
import TrainingStatusChart from '../components/analysis/TrainingStatusChart';
import ImprovementSummary from '../components/analysis/ImprovementSummary';
import { analyzeRaceTimes, analyzeTrainingStatus, getImprovementAnalysis } from '../services/analysis.service';
import './AnalysisPage.css';

function AnalysisPage() {
  const { user } = useUser();
  const { availableData, isLoading: dataLoading } = useData();
  
  const [selectedDistance, setSelectedDistance] = useState('5K');
  const [timeFrame, setTimeFrame] = useState(90);
  const [raceTimeData, setRaceTimeData] = useState(null);
  const [trainingStatusData, setTrainingStatusData] = useState(null);
  const [improvementData, setImprovementData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalysisData = async () => {
      try {
        setIsLoading(true);
        
        // Check if we have required data
        if (!availableData || !availableData.race_predictions || !availableData.training_history) {
          setError('Keine Daten verfügbar. Bitte laden Sie zuerst Ihre Garmin-Daten hoch.');
          return;
        }
        
        // Fetch race times analysis
        const raceData = await analyzeRaceTimes(selectedDistance, timeFrame, user?.id);
        setRaceTimeData(raceData);
        
        // Fetch training status analysis
        const statusData = await analyzeTrainingStatus(timeFrame, user?.id);
        setTrainingStatusData(statusData);
        
        // Fetch improvement analysis
        const improvementData = await getImprovementAnalysis(selectedDistance, null, null, user?.id);
        setImprovementData(improvementData);
        
        setError(null);
      } catch (err) {
        console.error('Analysefehler:', err);
        setError('Fehler beim Laden der Analysedaten: ' + err.message);
      } finally {
        setIsLoading(false);
      }
    };

    if (!dataLoading && availableData) {
      fetchAnalysisData();
    }
  }, [availableData, dataLoading, selectedDistance, timeFrame, user]);

  const handleDistanceChange = (e) => {
    setSelectedDistance(e.target.value);
  };

  const handleTimeFrameChange = (e) => {
    setTimeFrame(parseInt(e.target.value, 10));
  };

  // Render loading state
  if (dataLoading || isLoading) {
    return <div className="loading-container">Analysedaten werden geladen...</div>;
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
    <div className="analysis-page">
      <h1>Laufleistungsanalyse</h1>
      
      <div className="analysis-controls">
        <div className="control-group">
          <label htmlFor="distance-select">Distanz:</label>
          <select 
            id="distance-select" 
            value={selectedDistance} 
            onChange={handleDistanceChange}
          >
            <option value="5K">5K</option>
            <option value="10K">10K</option>
            <option value="Half">Halbmarathon</option>
            <option value="Marathon">Marathon</option>
          </select>
        </div>
        
        <div className="control-group">
          <label htmlFor="timeframe-select">Zeitraum:</label>
          <select 
            id="timeframe-select" 
            value={timeFrame} 
            onChange={handleTimeFrameChange}
          >
            <option value="30">30 Tage</option>
            <option value="90">90 Tage</option>
            <option value="180">180 Tage</option>
            <option value="365">1 Jahr</option>
          </select>
        </div>
      </div>
      
      <div className="analysis-grid">
        <div className="analysis-item race-time-chart">
          <h2>{selectedDistance} Rennzeit-Trend</h2>
          {raceTimeData?.plot_data ? (
            <RaceTimeChart data={raceTimeData.plot_data} distance={selectedDistance} />
          ) : (
            <p>Keine Renndaten verfügbar</p>
          )}
        </div>
        
        <div className="analysis-item training-status-chart">
          <h2>Trainingsstatus-Entwicklung</h2>
          {trainingStatusData?.daily_status ? (
            <TrainingStatusChart data={trainingStatusData} />
          ) : (
            <p>Keine Trainingsstatus-Daten verfügbar</p>
          )}
        </div>
        
        <div className="analysis-item improvement-summary">
          <h2>Verbesserungsanalyse</h2>
          {improvementData && !improvementData.insufficient_data ? (
            <ImprovementSummary data={improvementData} />
          ) : (
            <p>Nicht genügend Daten für eine Verbesserungsanalyse</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default AnalysisPage;
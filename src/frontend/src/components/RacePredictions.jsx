// src/frontend/components/dashboard/RacePredictions.jsx
import React from 'react';
import './RacePredictions.css';

// Definiere die Komponente als normale Funktion
function RacePredictions({ predictions }) {
  if (!predictions) return null;
  
  return (
    <div className="race-predictions-container">
      <div className="prediction-cards">
        <div className="prediction-card">
          <h3>5K</h3>
          <div className="time">{predictions['5K'] || 'N/A'}</div>
        </div>
        
        <div className="prediction-card">
          <h3>10K</h3>
          <div className="time">{predictions['10K'] || 'N/A'}</div>
        </div>
        
        <div className="prediction-card">
          <h3>Halbmarathon</h3>
          <div className="time">{predictions['Half Marathon'] || 'N/A'}</div>
        </div>
        
        <div className="prediction-card">
          <h3>Marathon</h3>
          <div className="time">{predictions['Marathon'] || 'N/A'}</div>
        </div>
      </div>
      
      <div className="predictions-footer">
        <p>Basierend auf Ihren jüngsten Trainingsaktivitäten</p>
      </div>
    </div>
  );
}

// Hier nur ein einziger default export
export default RacePredictions;
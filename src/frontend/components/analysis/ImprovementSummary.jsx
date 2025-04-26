// src/frontend/components/analysis/ImprovementSummary.jsx
import React from 'react';
import './ImprovementSummary.css';

function ImprovementSummary({ data }) {
  if (!data) return null;
  
  // Format dates
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE');
  };
  
  // Improvement direction and description
  const getImprovementStatus = () => {
    if (data.improved) {
      return {
        direction: 'verbessert',
        class: 'improved',
        icon: '↑',
      };
    } else {
      return {
        direction: 'verschlechtert',
        class: 'worsened',
        icon: '↓',
      };
    }
  };
  
  const improvementStatus = getImprovementStatus();
  
  return (
    <div className={`improvement-summary ${improvementStatus.class}`}>
      <div className="improvement-header">
        <div className="distance-label">{data.distance}</div>
        <div className="improvement-percentage">
          <span className="percentage-value">
            {Math.abs(data.percent_improvement).toFixed(2)}%
          </span>
          <span className="direction-icon">{improvementStatus.icon}</span>
        </div>
      </div>
      
      <div className="improvement-details">
        <div className="time-comparison">
          <div className="start-time">
            <span className="time-label">Startzeit:</span>
            <span className="time-value">{data.start_time}</span>
            <span className="time-date">{formatDate(data.start_date)}</span>
          </div>
          
          <div className="improvement-arrow">→</div>
          
          <div className="end-time">
            <span className="time-label">Endzeit:</span>
            <span className="time-value">{data.end_time}</span>
            <span className="time-date">{formatDate(data.end_date)}</span>
          </div>
        </div>
        
        <div className="time-difference">
          <span className="difference-label">Zeitdifferenz:</span>
          <span className="difference-value">{data.time_difference}</span>
        </div>
      </div>
    </div>
  );
}

export default ImprovementSummary;
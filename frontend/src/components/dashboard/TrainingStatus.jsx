// src/frontend/components/dashboard/TrainingStatus.jsx
import React from 'react';
import './TrainingStatus.css';

function TrainingStatus({ statusData }) {
  if (!statusData || !statusData.status_counts) return null;
  
  // Get the status counts and sort them
  const statuses = Object.entries(statusData.status_counts).sort((a, b) => b[1] - a[1]);
  
  // Determine the current/most frequent status
  const currentStatus = statuses.length > 0 ? statuses[0][0] : 'Unbekannt';
  
  // Get status color based on status
  const getStatusColor = (status) => {
    switch (status.toLowerCase()) {
      case 'productive':
        return '#4CAF50'; // Green
      case 'peaking':
        return '#2196F3'; // Blue
      case 'recovery':
        return '#FF9800'; // Orange
      case 'detraining':
        return '#F44336'; // Red
      case 'maintaining':
        return '#9C27B0'; // Purple
      case 'unproductive':
        return '#FF5722'; // Deep Orange
      default:
        return '#757575'; // Grey
    }
  };
  
  return (
    <div className="training-status-container">
      <div className="current-status" style={{ backgroundColor: getStatusColor(currentStatus) }}>
        <h3>Aktueller Status</h3>
        <div className="status-value">{currentStatus}</div>
      </div>
      
      <div className="status-distribution">
        <h3>Status-Verteilung</h3>
        <div className="status-bars">
          {statuses.map(([status, count]) => (
            <div className="status-bar-item" key={status}>
              <div className="status-label">{status}</div>
              <div className="status-bar-container">
                <div 
                  className="status-bar" 
                  style={{ 
                    width: `${Math.min(100, count * 10)}%`,
                    backgroundColor: getStatusColor(status)
                  }}
                ></div>
                <span className="status-count">{count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default TrainingStatus;
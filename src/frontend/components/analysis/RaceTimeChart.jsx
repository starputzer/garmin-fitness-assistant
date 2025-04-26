// src/frontend/components/analysis/RaceTimeChart.jsx
import React from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import './RaceTimeChart.css';

// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

function RaceTimeChart({ data, distance }) {
  if (!data || !data.dates || !data.times || data.dates.length === 0) {
    return <p>Keine Daten verfügbar</p>;
  }
  
  // Format seconds to MM:SS or HH:MM:SS
  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (minutes >= 60) {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      return `${hours}:${remainingMinutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };
  
  // Get distance title
  const getDistanceTitle = () => {
    switch (distance) {
      case '5K': return '5K';
      case '10K': return '10K';
      case 'Half': return 'Halbmarathon';
      case 'Marathon': return 'Marathon';
      default: return distance;
    }
  };
  
  // Prepare chart data
  const chartData = {
    labels: data.dates,
    datasets: [
      {
        label: `${getDistanceTitle()} Zeit`,
        data: data.times,
        borderColor: '#2196F3',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  };
  
  // Chart options with inverted Y axis (lower time is better)
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        reverse: true, // Invert the Y axis so lower times are higher
        ticks: {
          callback: (value) => formatTime(value),
        },
        title: {
          display: true,
          text: 'Zeit',
        },
      },
      x: {
        title: {
          display: true,
          text: 'Datum',
        },
      },
    },
    plugins: {
      tooltip: {
        callbacks: {
          label: (context) => {
            return `Zeit: ${formatTime(context.raw)}`;
          },
        },
      },
    },
  };
  
  return (
    <div className="race-time-chart">
      <div className="chart-container">
        <Line data={chartData} options={chartOptions} />
      </div>
    </div>
  );
}

export default RaceTimeChart;
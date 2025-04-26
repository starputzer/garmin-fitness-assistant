// src/frontend/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import AnalysisPage from './pages/AnalysisPage';
import TrainingPlanPage from './pages/TrainingPlanPage';
import RecommendationsPage from './pages/RecommendationsPage';
import { DataProvider } from './context/DataContext';
import { UserProvider } from './context/UserContext';
import './App.css';

function App() {
  return (
    <UserProvider>
      <DataProvider>
        <Router>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<DashboardPage />} />
              <Route path="upload" element={<UploadPage />} />
              <Route path="analysis" element={<AnalysisPage />} />
              <Route path="training-plan" element={<TrainingPlanPage />} />
              <Route path="recommendations" element={<RecommendationsPage />} />
            </Route>
          </Routes>
        </Router>
      </DataProvider>
    </UserProvider>
  );
}

export default App;
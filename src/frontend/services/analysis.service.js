// src/frontend/services/analysis.service.js
import { apiRequest } from './api.service';

/**
 * Analyse der Rennzeiten abrufen
 */
export async function analyzeRaceTimes(distance = '5K', days = 90, userId = 'default') {
  return apiRequest(`/analyze/race_times/?distance=${distance}&days=${days}&user_id=${userId}`);
}

/**
 * Analyse des Trainingsstatus abrufen
 */
export async function analyzeTrainingStatus(days = 90, userId = 'default') {
  return apiRequest(`/analyze/training_status/?days=${days}&user_id=${userId}`);
}

/**
 * Verbesserungsanalyse für eine bestimmte Distanz abrufen
 */
export async function getImprovementAnalysis(distance = '5K', startDate, endDate, userId = 'default') {
  let url = `/analyze/improvement/?distance=${distance}&user_id=${userId}`;
  
  if (startDate) {
    url += `&start_date=${startDate}`;
  }
  
  if (endDate) {
    url += `&end_date=${endDate}`;
  }
  
  return apiRequest(url);
}
// src/frontend/services/training.service.js
import { apiRequest } from './api.service';

/**
 * Trainingsempfehlungen abrufen
 */
export async function getRecommendations(userId = 'default') {
  return apiRequest(`/recommendations/?user_id=${userId}`);
}

/**
 * Trainingsplan erstellen
 */
export async function createTrainingPlan(goalDistance, targetTime, weeks = 8, sessionsPerWeek = 4, userId = 'default') {
  return apiRequest('/training_plan/', {
    method: 'POST',
    body: JSON.stringify({
      goal_distance: goalDistance,
      target_time: targetTime,
      weeks: weeks,
      sessions_per_week: sessionsPerWeek,
      user_id: userId
    })
  });
}
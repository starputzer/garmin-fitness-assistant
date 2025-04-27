// src/frontend/services/api.service.js
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

/**
 * Allgemeine Funktion für API-Anfragen
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const requestOptions = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
  };
  
  try {
    const response = await fetch(url, requestOptions);
    
    // Fehlerbehandlung für nicht-erfolgreiche Antworten
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(
        errorData?.detail || `API-Anfrage fehlgeschlagen: ${response.status} ${response.statusText}`
      );
    }
    
    // Überprüfe, ob die Antwort JSON enthält
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }
    
    return await response.text();
  } catch (error) {
    console.error('API-Anfragefehler:', error);
    throw error;
  }
}

/**
 * Liste der verfügbaren Daten abrufen
 */
export async function listAvailableData(userId = 'default') {
  return apiRequest(`/data/list/?user_id=${userId}`);
}

export { apiRequest };
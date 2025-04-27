// src/frontend/services/upload.service.js
import { apiRequest } from './api.service';

/**
 * Garmin-Daten hochladen
 */
export async function uploadGarminData(files, userId = 'default') {
  const formData = new FormData();
  
  // Dateien hinzufügen
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }
  
  // User-ID hinzufügen
  formData.append('user_id', userId);
  
  return apiRequest('/upload/', {
    method: 'POST',
    headers: {
      // Wichtig: Keine Content-Type setzen, damit der Browser den Boundary-String korrekt setzt
    },
    body: formData
  });
}
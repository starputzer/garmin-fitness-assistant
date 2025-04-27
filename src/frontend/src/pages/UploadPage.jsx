// src/frontend/pages/UploadPage.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { useData } from '../context/DataContext';
import FileUploader from '../components/upload/FileUploader';
import UploadStatus from '../components/upload/UploadStatus';
import DataPreview from '../components/upload/DataPreview';
import { uploadGarminData } from '../services/upload.service';
import './UploadPage.css';

function UploadPage() {
  const navigate = useNavigate();
  const { user } = useUser();
  const { refreshData } = useData();
  
  const [files, setFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [previewData, setPreviewData] = useState(null);

  const handleFileChange = (selectedFiles) => {
    setFiles(selectedFiles);
    setPreviewData(null); // Reset preview when new files are selected
    
    // Preview first file if it's JSON
    if (selectedFiles.length > 0 && selectedFiles[0].type === 'application/json') {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result);
          // Just show a sample of the data
          setPreviewData({
            filename: selectedFiles[0].name,
            sample: data.slice(0, 5)
          });
        } catch (err) {
          console.error('Error parsing JSON preview:', err);
        }
      };
      reader.readAsText(selectedFiles[0]);
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setUploadStatus({
        success: false,
        message: 'Bitte wählen Sie zuerst Dateien aus.'
      });
      return;
    }

    try {
      setIsUploading(true);
      setUploadProgress(0);
      
      // Upload simulation with progress
      const simulateProgress = () => {
        setUploadProgress(prev => {
          if (prev < 90) return prev + 10;
          return prev;
        });
      };
      
      const progressInterval = setInterval(simulateProgress, 500);
      
      // Perform actual upload
      const result = await uploadGarminData(files, user?.id);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      setUploadStatus({
        success: true,
        message: 'Dateien erfolgreich hochgeladen. Daten werden verarbeitet.',
        files: result.files
      });
      
      // Refresh available data list
      await refreshData();
      
      // Automatically navigate to dashboard after successful upload
      setTimeout(() => {
        navigate('/');
      }, 3000);
      
    } catch (err) {
      setUploadStatus({
        success: false,
        message: `Fehler beim Hochladen: ${err.message}`
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="upload-page">
      <h1>Garmin-Daten hochladen</h1>
      
      <div className="upload-instructions">
        <h2>Anleitung</h2>
        <p>Bitte laden Sie Ihre Garmin Connect Export-Dateien hoch. Unterstützte Dateitypen:</p>
        <ul>
          <li>RunRacePredictions_*.json - Enthält Rennprognosen</li>
          <li>TrainingHistory_*.json - Enthält Trainingsverlauf</li>
          <li>MetricsHeatAltitudeAcclimation_*.json - Enthält Hitze- und Höhenakklimatisierungsmetriken</li>
          <li>SummarizedActivities_*.json - Enthält Zusammenfassungen Ihrer Aktivitäten</li>
        </ul>
      </div>
      
      <FileUploader 
        onFileChange={handleFileChange} 
        acceptedTypes=".json"
        multiple={true}
      />
      
      {files.length > 0 && (
        <div className="selected-files">
          <h3>Ausgewählte Dateien:</h3>
          <ul>
            {Array.from(files).map((file, index) => (
              <li key={index}>
                {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </li>
            ))}
          </ul>
          
          <button 
            className="upload-button"
            onClick={handleUpload}
            disabled={isUploading}
          >
            {isUploading ? 'Uploading...' : 'Dateien hochladen'}
          </button>
        </div>
      )}
      
      {isUploading && (
        <div className="upload-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
          <p>{uploadProgress}% abgeschlossen</p>
        </div>
      )}
      
      {uploadStatus && (
        <UploadStatus status={uploadStatus} />
      )}
      
      {previewData && (
        <DataPreview data={previewData} />
      )}
    </div>
  );
}

export default UploadPage;
// src/frontend/components/upload/UploadStatus.jsx
import React from 'react';
import './UploadStatus.css';

function UploadStatus({ status }) {
  if (!status) return null;
  
  return (
    <div className={`upload-status ${status.success ? 'success' : 'error'}`}>
      <div className="status-icon">
        {status.success ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 13L9 17L19 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 18L18 6M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )}
      </div>
      
      <div className="status-message">
        {status.message}
      </div>
      
      {status.success && status.files && (
        <div className="uploaded-files">
          <h4>Hochgeladene Dateien:</h4>
          <ul>
            {status.files.map((file, index) => (
              <li key={index}>{file}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default UploadStatus;
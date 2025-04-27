// src/frontend/components/upload/FileUploader.jsx
import React, { useRef, useState } from 'react';
import './FileUploader.css';

function FileUploader({ onFileChange, acceptedTypes = '*', multiple = false }) {
  const fileInputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  
  const handleFileSelect = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileChange(files);
    }
  };
  
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileChange(e.dataTransfer.files);
    }
  };
  
  const openFileSelector = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };
  
  return (
    <div 
      className={`file-uploader ${dragActive ? 'drag-active' : ''}`}
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      onClick={openFileSelector}
    >
      <input 
        type="file" 
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept={acceptedTypes}
        multiple={multiple}
        className="file-input"
      />
      
      <div className="upload-content">
        <div className="upload-icon">
          <svg width="50" height="50" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M7 10V9C7 6.23858 9.23858 4 12 4C14.7614 4 17 6.23858 17 9V10C19.2091 10 21 11.7909 21 14C21 16.2091 19.2091 18 17 18H7C4.79086 18 3 16.2091 3 14C3 11.7909 4.79086 10 7 10Z" stroke="currentColor" strokeWidth="2"/>
            <path d="M12 12L12 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M10 14L12 12L14 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <div className="upload-text">
          <p className="primary-text">
            Dateien hierher ziehen oder klicken, um auszuwählen
          </p>
          <p className="secondary-text">
            {multiple 
              ? `Unterstützte Dateitypen: ${acceptedTypes}`
              : `Unterstützte Dateitypen: ${acceptedTypes} (max. 1 Datei)`}
          </p>
        </div>
      </div>
    </div>
  );
}

export default FileUploader;
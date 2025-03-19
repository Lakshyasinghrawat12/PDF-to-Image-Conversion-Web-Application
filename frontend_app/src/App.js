import React, { useState, useEffect } from 'react';
import api from './api';
import './App.css';

const App = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);
  const [serverStatus, setServerStatus] = useState('checking');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [convertingFiles, setConvertingFiles] = useState(false);
  const [conversionStatus, setConversionStatus] = useState(null);
  const [conversionProgress, setConversionProgress] = useState(0);
  const [conversionSuccess, setConversionSuccess] = useState(false);

  // Check server status on component mount
  useEffect(() => {
    checkServerStatus();
  }, []);

  const checkServerStatus = async () => {
    setServerStatus('checking');
    try {
      await api.get('/health', { timeout: 5000 });
      setServerStatus('online');
    } catch (error) {
      console.error('Server check failed:', error);
      setServerStatus('offline');
    }
  };

  const handleFolderSelect = (e) => {
    const folderFiles = Array.from(e.target.files).filter(file => 
      file.name.toLowerCase().endsWith('.pdf')
    );
    setFiles(folderFiles);
    setUploadResult(null);
    setError(null);
    setUploadProgress(0);
  };

  const getRelativePath = (file) => {
    // Extract the relative path from webkitRelativePath
    return file.webkitRelativePath || file.name;
  };

  const uploadFiles = async () => {
    if (files.length === 0) {
      setError("Please select a folder containing PDF files");
      return;
    }

    if (serverStatus !== 'online') {
      setError("Server appears to be offline. Please check your connection.");
      return;
    }

    setUploading(true);
    setError(null);
    setUploadProgress(0);
    setUploadResult(null);
    setConversionStatus(null);
    setConversionSuccess(false);
    
    const formData = new FormData();
    files.forEach(file => {
      const relativePath = getRelativePath(file);
      formData.append('files', file, relativePath);
    });

    try {
      const response = await api.post("/upload-files/", formData, {
        timeout: 120000, // 2 minute timeout for larger uploads
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(percentCompleted);
        }
      });

      setUploading(false);
      setUploadResult({
        message: "Files uploaded successfully!",
        filenames: response.data.filenames
      });
      
      // Automatically start conversion after successful upload
      startConversion();
      
    } catch (error) {
      console.error('Error uploading files:', error);
      let errorMessage = 'Error uploading files. Please try again.';
      
      if (error.code === 'ERR_NETWORK') {
        errorMessage = 'Network error: Please check if the server is running at http://localhost:8000';
      } else if (error.response) {
        errorMessage = `Server error: ${error.response.status} ${error.response.statusText}`;
        if (error.response.data && error.response.data.detail) {
          errorMessage += ` - ${error.response.data.detail}`;
        }
      } else if (error.request) {
        errorMessage = 'No response from server. Please check your connection.';
      }
      
      setError(errorMessage);
    }
  };

  const startConversion = async () => {
    setConvertingFiles(true);
    setError(null);
    setConversionSuccess(false);
    
    try {
      // Start conversion
      const response = await api.post('/convert-pdfs/', {
        folder_path: '' // Empty for all files, or specify subfolder
      });
      
      // Poll for status updates
      const statusInterval = setInterval(async () => {
        try {
          const statusResponse = await api.get(`/conversion-status/${response.data.task_id}`);
          const status = statusResponse.data;
          
          setConversionStatus(status);
          const progress = Math.round((status.converted + status.failed) / status.total * 100);
          setConversionProgress(progress);
          
          if (status.status === 'completed') {
            clearInterval(statusInterval);
            setConvertingFiles(false);
            setConversionSuccess(true);
          }
        } catch (error) {
          console.error('Error checking conversion status:', error);
          clearInterval(statusInterval);
          setConvertingFiles(false);
          setError('Error checking conversion status');
        }
      }, 2000); // Check every 2 seconds
      
    } catch (error) {
      console.error('Error converting files:', error);
      setConvertingFiles(false);
      setError('Error converting files to images');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>PDF Upload Portal</h1>
        
        <div className="server-status">
          Server Status: 
          {serverStatus === 'checking' && <span className="status-checking">Checking...</span>}
          {serverStatus === 'online' && <span className="status-online">Online</span>}
          {serverStatus === 'offline' && (
            <>
              <span className="status-offline">Offline</span>
              <button onClick={checkServerStatus} className="retry-button">Retry Connection</button>
            </>
          )}
        </div>
        
        <div className="upload-section">
          <h2>Upload PDF Folder</h2>
          <input 
            type="file" 
            webkitdirectory="true" 
            directory="true" 
            multiple 
            onChange={handleFolderSelect}
            className="file-input"
            disabled={serverStatus !== 'online'}
          />
          
          <div className="selected-files">
            <h3>Selected PDF Files: {files.length}</h3>
            {files.length > 0 ? (
              <ul>
                {files.map((file, index) => (
                  <li key={index}>
                    <div className="file-path">{getRelativePath(file)}</div>
                    <div className="file-size">{Math.round(file.size / 1024)} KB</div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="no-files">Select a folder containing PDFs to upload</p>
            )}
          </div>
          
          <button 
            onClick={uploadFiles} 
            disabled={files.length === 0 || uploading || serverStatus !== 'online'}
            className="upload-button"
          >
            {uploading ? `Uploading... ${uploadProgress}%` : 'Upload Folder'}
          </button>
          
          {uploading && (
            <div className="progress-bar-container">
              <div 
                className="progress-bar" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          )}
          
          {error && <div className="error-message">{error}</div>}
          
          {uploadResult && (
            <div className="success-message">
              <h3>Upload Successful!</h3>
              <p>Uploaded {uploadResult.filenames.length} files:</p>
              <ul className="uploaded-files-list">
                {uploadResult.filenames.map((filename, index) => (
                  <li key={index}>{filename}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {uploadResult && (
          <div className="conversion-section">
            <h2>Automatic PDF to Image Conversion</h2>
            
            {/* Show processing status while converting */}
            {convertingFiles && (
              <>
                <p>Converting PDF files to images...</p>
                <div className="progress-bar-container">
                  <div 
                    className="progress-bar" 
                    style={{ width: `${conversionProgress}%` }}
                  ></div>
                </div>
              </>
            )}
            
            {/* Show conversion status */}
            {conversionStatus && (
              <div className="conversion-status">
                <p>Status: {conversionStatus.status}</p>
                <p>Converted: {conversionStatus.converted} / {conversionStatus.total}</p>
                {conversionStatus.failed > 0 && (
                  <p className="conversion-errors">Failed: {conversionStatus.failed}</p>
                )}
              </div>
            )}

            {/* Show success message when done */}
            {conversionSuccess && (
              <div className="success-message">
                <h3>Conversion Complete!</h3>
                <p>All PDFs have been automatically converted to images.</p>
              </div>
            )}
          </div>
        )}
      </header>
    </div>
  );
};

export default App;

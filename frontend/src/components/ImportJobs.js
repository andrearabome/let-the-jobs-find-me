import React, { useRef } from 'react';
import axios from 'axios';
import './ImportJobs.css';

function ImportJobs({ onJobsImported }) {
  const fileInputRef = useRef(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [message, setMessage] = React.useState('');

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setMessage('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post('/api/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setMessage(`✓ Imported ${res.data.imported} jobs successfully!`);
      onJobsImported();

      // Clear input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      // Clear message after 3 seconds
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage('✗ Error importing file. Please check the format.');
      console.error('Import error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddManually = () => {
    // Could be extended for manual job addition
    alert('Feature coming soon: Add jobs manually via form');
  };

  return (
    <div className="import-panel">
      <h3>Import Jobs</h3>

      <div className="import-section">
        <p className="import-info">Upload a CSV or JSON file with job listings</p>

        <div className="file-input-wrapper">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.json"
            onChange={handleFileChange}
            disabled={isLoading}
            className="file-input"
            id="file-input"
          />
          <label htmlFor="file-input" className="file-input-label">
            {isLoading ? 'Uploading...' : 'Choose File'}
          </label>
        </div>

        {message && (
          <div className={`import-message ${message.startsWith('✓') ? 'success' : 'error'}`}>
            {message}
          </div>
        )}

        <p className="file-format-help">
          <strong>CSV Format:</strong> title, company, location, role, description, url, salary
        </p>
      </div>

      <button onClick={handleAddManually} className="add-manually-btn">
        + Add Job Manually
      </button>
    </div>
  );
}

export default ImportJobs;

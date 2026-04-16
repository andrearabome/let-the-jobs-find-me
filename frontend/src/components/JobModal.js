import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './JobModal.css';

function JobModal({ job, isBookmarked, onClose, onToggleBookmark }) {
  const [application, setApplication] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    status: 'interested',
    notes: '',
    appliedDate: ''
  });

  useEffect(() => {
    fetchApplication();
  }, [job.id]);

  const fetchApplication = async () => {
    try {
      const res = await axios.get(`/api/applications/${job.id}`);
      if (res.data && res.data.id) {
        setApplication(res.data);
        setFormData({
          status: res.data.status,
          notes: res.data.notes,
          appliedDate: res.data.appliedDate
        });
      }
    } catch (error) {
      console.error('Error fetching application:', error);
    }
  };

  const handleSaveApplication = async () => {
    try {
      await axios.post('/api/applications', {
        jobId: job.id,
        ...formData
      });
      setIsEditing(false);
      fetchApplication();
    } catch (error) {
      console.error('Error saving application:', error);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this job?')) {
      try {
        await axios.delete(`/api/jobs/${job.id}`);
        onClose();
      } catch (error) {
        console.error('Error deleting job:', error);
      }
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2>{job.title}</h2>
            <p className="modal-company">{job.company}</p>
          </div>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <div className="modal-section">
            <h3>Job Details</h3>
            <div className="details-grid">
              <div className="detail-item">
                <strong>Location:</strong>
                <p>{job.location}</p>
              </div>
              <div className="detail-item">
                <strong>Role Type:</strong>
                <p>{job.role}</p>
              </div>
              {job.salary && (
                <div className="detail-item">
                  <strong>Salary:</strong>
                  <p>{job.salary}</p>
                </div>
              )}
              <div className="detail-item">
                <strong>Posted Date:</strong>
                <p>{new Date(job.postedDate).toLocaleDateString()}</p>
              </div>
            </div>
          </div>

          {job.description && (
            <div className="modal-section">
              <h3>Description</h3>
              <p className="job-full-description">{job.description}</p>
            </div>
          )}

          {job.url && (
            <div className="modal-section">
              <a href={job.url} target="_blank" rel="noopener noreferrer" className="job-url-btn">
                View Original Posting →
              </a>
            </div>
          )}

          <div className="modal-section">
            <h3>Application Tracking</h3>
            {!isEditing ? (
              <div className="application-display">
                {application?.status && (
                  <>
                    <p><strong>Status:</strong> <span className={`status-badge ${application.status}`}>{application.status}</span></p>
                    {application.notes && <p><strong>Notes:</strong> {application.notes}</p>}
                    {application.appliedDate && <p><strong>Applied Date:</strong> {application.appliedDate}</p>}
                  </>
                )}
                {!application?.status && <p className="no-application">No application tracked yet</p>}
                <button onClick={() => setIsEditing(true)} className="edit-btn">
                  {application?.status ? 'Update Application' : 'Track Application'}
                </button>
              </div>
            ) : (
              <div className="application-form">
                <div className="form-group">
                  <label>Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  >
                    <option value="interested">Interested</option>
                    <option value="applied">Applied</option>
                    <option value="interview">Interview Scheduled</option>
                    <option value="offered">Offer Received</option>
                    <option value="rejected">Rejected</option>
                    <option value="accepted">Accepted</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Applied Date</label>
                  <input
                    type="date"
                    value={formData.appliedDate}
                    onChange={(e) => setFormData({ ...formData, appliedDate: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label>Notes</label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="Add notes about this application..."
                    rows="4"
                  />
                </div>

                <div className="form-actions">
                  <button onClick={handleSaveApplication} className="save-btn">Save</button>
                  <button onClick={() => setIsEditing(false)} className="cancel-btn">Cancel</button>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button
            className={`bookmark-action ${isBookmarked ? 'bookmarked' : ''}`}
            onClick={() => onToggleBookmark(job.id)}
          >
            {isBookmarked ? '★ Unbookmark' : '☆ Bookmark'}
          </button>
          <button onClick={handleDelete} className="delete-btn">Delete</button>
        </div>
      </div>
    </div>
  );
}

export default JobModal;

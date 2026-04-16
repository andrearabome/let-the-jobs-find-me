import React from 'react';
import './JobCard.css';

function JobCard({ job, isBookmarked, onSelect, onToggleBookmark }) {
  const handleBookmarkClick = (e) => {
    e.stopPropagation();
    onToggleBookmark(job.id);
  };

  return (
    <div className="job-card" onClick={() => onSelect(job)}>
      <div className="job-card-header">
        <div className="job-card-title">
          <h3>{job.title}</h3>
          <p className="company-name">{job.company}</p>
        </div>
        <button
          className={`bookmark-btn ${isBookmarked ? 'bookmarked' : ''}`}
          onClick={handleBookmarkClick}
          title={isBookmarked ? 'Remove bookmark' : 'Bookmark this job'}
        >
          ★
        </button>
      </div>

      <div className="job-card-meta">
        <span className="meta-item location">📍 {job.location}</span>
        <span className="meta-item role">{job.role}</span>
        {job.salary && <span className="meta-item salary">💰 {job.salary}</span>}
      </div>

      {job.description && (
        <p className="job-description">{job.description.substring(0, 150)}...</p>
      )}

      <div className="job-card-footer">
        <small className="posted-date">
          Posted: {new Date(job.postedDate).toLocaleDateString()}
        </small>
        <span className="view-details">View Details →</span>
      </div>
    </div>
  );
}

export default JobCard;

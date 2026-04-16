import React from 'react';
import './JobList.css';
import JobCard from './JobCard';

function JobList({ jobs, bookmarks, onSelectJob, onToggleBookmark }) {
  if (jobs.length === 0) {
    return (
      <div className="empty-state">
        <p>No jobs found. Try adjusting your filters or import some jobs!</p>
      </div>
    );
  }

  return (
    <div className="job-list">
      {jobs.map(job => (
        <JobCard
          key={job.id}
          job={job}
          isBookmarked={bookmarks.includes(job.id)}
          onSelect={onSelectJob}
          onToggleBookmark={onToggleBookmark}
        />
      ))}
    </div>
  );
}

export default JobList;

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import JobList from './components/JobList';
import Filters from './components/Filters';
import JobModal from './components/JobModal';
import ImportJobs from './components/ImportJobs';

function App() {
  const [jobs, setJobs] = useState([]);
  const [filteredJobs, setFilteredJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [filters, setFilters] = useState({
    role: '',
    location: '',
    search: '',
    view: 'all' // 'all', 'bookmarked'
  });
  const [filterOptions, setFilterOptions] = useState({ roles: [], locations: [] });
  const [bookmarks, setBookmarks] = useState([]);

  // Fetch filter options
  useEffect(() => {
    axios.get('/api/filters').then((res) => {
      setFilterOptions(res.data);
    });
  }, []);

  // Fetch jobs
  useEffect(() => {
    fetchJobs();
  }, []);

  // Fetch bookmarks
  useEffect(() => {
    axios.get('/api/bookmarks').then((res) => {
      setBookmarks(res.data.map(j => j.id));
    });
  }, []);

  // Apply filters
  useEffect(() => {
    let result = jobs;

    if (filters.role) {
      result = result.filter(job => job.role === filters.role);
    }

    if (filters.location) {
      result = result.filter(job => job.location === filters.location);
    }

    if (filters.search) {
      result = result.filter(job =>
        job.title.toLowerCase().includes(filters.search.toLowerCase()) ||
        job.company.toLowerCase().includes(filters.search.toLowerCase())
      );
    }

    if (filters.view === 'bookmarked') {
      result = result.filter(job => bookmarks.includes(job.id));
    }

    setFilteredJobs(result);
  }, [jobs, filters, bookmarks]);

  const fetchJobs = async () => {
    try {
      const res = await axios.get('/api/jobs');
      setJobs(res.data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  const handleJobSelect = (job) => {
    setSelectedJob(job);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedJob(null);
    fetchJobs();
  };

  const handleJobsImported = () => {
    fetchJobs();
  };

  const handleToggleBookmark = async (jobId) => {
    try {
      if (bookmarks.includes(jobId)) {
        await axios.delete(`/api/bookmarks/${jobId}`);
        setBookmarks(bookmarks.filter(id => id !== jobId));
      } else {
        await axios.post('/api/bookmarks', { jobId });
        setBookmarks([...bookmarks, jobId]);
      }
    } catch (error) {
      console.error('Error toggling bookmark:', error);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Let The Jobs Find Me</h1>
        <p>Track UI/UX, Research, and Analyst opportunities</p>
      </header>

      <div className="App-container">
        <aside className="sidebar">
          <ImportJobs onJobsImported={handleJobsImported} />
          <Filters
            filters={filters}
            filterOptions={filterOptions}
            onFilterChange={handleFilterChange}
          />
        </aside>

        <main className="main-content">
          <div className="jobs-header">
            <h2>
              {filters.view === 'bookmarked' ? 'Bookmarked Jobs' : 'All Jobs'}
              <span className="job-count">({filteredJobs.length})</span>
            </h2>
            <div className="view-toggle">
              <button
                className={`toggle-btn ${filters.view === 'all' ? 'active' : ''}`}
                onClick={() => handleFilterChange({ view: 'all' })}
              >
                All Jobs
              </button>
              <button
                className={`toggle-btn ${filters.view === 'bookmarked' ? 'active' : ''}`}
                onClick={() => handleFilterChange({ view: 'bookmarked' })}
              >
                Bookmarked
              </button>
            </div>
          </div>
          <JobList
            jobs={filteredJobs}
            bookmarks={bookmarks}
            onSelectJob={handleJobSelect}
            onToggleBookmark={handleToggleBookmark}
          />
        </main>
      </div>

      {showModal && (
        <JobModal
          job={selectedJob}
          isBookmarked={bookmarks.includes(selectedJob?.id)}
          onClose={handleCloseModal}
          onToggleBookmark={handleToggleBookmark}
        />
      )}
    </div>
  );
}

export default App;

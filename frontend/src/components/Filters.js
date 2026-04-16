import React from 'react';
import './Filters.css';

function Filters({ filters, filterOptions, onFilterChange }) {
  const handleRoleChange = (e) => {
    onFilterChange({ role: e.target.value });
  };

  const handleLocationChange = (e) => {
    onFilterChange({ location: e.target.value });
  };

  const handleSearchChange = (e) => {
    onFilterChange({ search: e.target.value });
  };

  const handleClearFilters = () => {
    onFilterChange({
      role: '',
      location: '',
      search: ''
    });
  };

  return (
    <div className="filters-panel">
      <h3>Filters</h3>

      <div className="filter-group">
        <label htmlFor="search">Search</label>
        <input
          id="search"
          type="text"
          placeholder="Job title or company..."
          value={filters.search}
          onChange={handleSearchChange}
          className="filter-input"
        />
      </div>

      <div className="filter-group">
        <label htmlFor="role">Role Type</label>
        <select
          id="role"
          value={filters.role}
          onChange={handleRoleChange}
          className="filter-select"
        >
          <option value="">All Roles</option>
          {filterOptions.roles?.map(role => (
            <option key={role} value={role}>
              {role}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="location">Location</label>
        <select
          id="location"
          value={filters.location}
          onChange={handleLocationChange}
          className="filter-select"
        >
          <option value="">All Locations</option>
          {filterOptions.locations?.map(location => (
            <option key={location} value={location}>
              {location}
            </option>
          ))}
        </select>
      </div>

      {(filters.role || filters.location || filters.search) && (
        <button onClick={handleClearFilters} className="clear-filters-btn">
          Clear Filters
        </button>
      )}
    </div>
  );
}

export default Filters;

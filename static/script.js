let currentView = 'all';
let currentJobId = null;
let allJobs = [];
let currentPage = 1;
let paginationData = null;
let searchDebounceTimer = null;
let currentJobsRequestController = null;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    removeLegacyStudentUi();
    initializeDarkMode();
    setupEventListeners();

    await clearNonBookmarkedJobsAndReload();
});

function removeLegacyStudentUi() {
    const studentFilter = document.getElementById('studentFilter');
    if (studentFilter) {
        const filterGroup = studentFilter.closest('.filter-group');
        if (filterGroup) {
            filterGroup.remove();
        } else {
            studentFilter.remove();
        }
    }

    const studentTab = document.querySelector('.toggle-btn[data-view="student"]');
    if (studentTab) {
        studentTab.remove();
    }

    const studentBadgeContainer = document.getElementById('studentBadgeContainer');
    if (studentBadgeContainer) {
        studentBadgeContainer.remove();
    }
}

function initializeDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        darkModeToggle.textContent = '☀️';
    }
    
    darkModeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        const isNowDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', isNowDark);
        darkModeToggle.textContent = isNowDark ? '☀️' : '🌙';
    });
}

function setupEventListeners() {
    // Scrape jobs
    const refreshJobsBtn = document.getElementById('refreshJobsBtn');
    const scrapeIndeedBtn = document.getElementById('scrapeIndeedBtn');
    const scrapeJobBankBtn = document.getElementById('scrapeJobBankBtn');
    if (refreshJobsBtn) {
        refreshJobsBtn.addEventListener('click', () => clearNonBookmarkedJobsAndReload());
    }
    if (scrapeIndeedBtn) {
        scrapeIndeedBtn.addEventListener('click', () => scrapeJobs('indeed'));
    }
    if (scrapeJobBankBtn) {
        scrapeJobBankBtn.addEventListener('click', () => scrapeJobs('jobbank'));
    }

    // Filters
    document.getElementById('search').addEventListener('input', () => {
        currentPage = 1;
        if (searchDebounceTimer) {
            clearTimeout(searchDebounceTimer);
        }
        searchDebounceTimer = setTimeout(() => {
            applyFilters();
        }, 300);
    });
    document.getElementById('roleFilter').addEventListener('change', () => {
        currentPage = 1;
        applyFilters();
    });
    document.getElementById('locationFilter').addEventListener('change', () => {
        currentPage = 1;
        applyFilters();
    });
    document.getElementById('clearFiltersBtn').addEventListener('click', clearFilters);

    // View toggle
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentView = e.target.dataset.view;
            currentPage = 1;
            displayJobs();
        });
    });

    // Modal
    document.querySelector('.close-btn').addEventListener('click', closeModal);
    document.getElementById('jobModal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('jobModal')) closeModal();
    });

    // Application tracking
    document.getElementById('trackAppBtn').addEventListener('click', showApplicationForm);
    document.getElementById('cancelAppBtn').addEventListener('click', hideApplicationForm);
    document.getElementById('saveAppBtn').addEventListener('click', saveApplication);

    // Bookmark
    document.getElementById('bookmarkBtn').addEventListener('click', toggleBookmark);

    // Delete
    document.getElementById('deleteJobBtn').addEventListener('click', deleteJob);
}

async function loadJobs() {
    try {
        if (currentJobsRequestController) {
            currentJobsRequestController.abort();
        }
        currentJobsRequestController = new AbortController();

        // Build query string with filters
        const params = new URLSearchParams();
        params.append('page', currentPage);
        
        const search = document.getElementById('search').value;
        const role = document.getElementById('roleFilter').value;
        const location = document.getElementById('locationFilter').value;
        
        if (search) params.append('search', search);
        if (role) params.append('role', role);
        if (location) params.append('location', location);
        
        const response = await fetch(`/api/jobs?${params}`, {
            signal: currentJobsRequestController.signal
        });
        const data = await response.json();
        
        allJobs = data.jobs;
        paginationData = data.pagination;
        displayJobs();
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.error('Error loading jobs:', error);
        }
    }
}

async function clearNonBookmarkedJobsAndReload() {
    try {
        await fetch('/api/jobs/clear-non-bookmarked', { method: 'POST' });
    } catch (error) {
        console.error('Error clearing non-bookmarked jobs:', error);
    }

    currentPage = 1;
    await loadJobs();
}

function displayJobs() {
    const jobsList = document.getElementById('jobsList');
    const paginationControls = document.getElementById('paginationControls');
    let jobs = allJobs;

    // Apply view filter (for bookmarked/student views)
    if (currentView === 'bookmarked') {
        jobs = jobs.filter(job => job.is_bookmarked);
        document.getElementById('jobsTitle').textContent = 'Bookmarked Jobs';
    } else {
        document.getElementById('jobsTitle').textContent = 'All Jobs';
    }

    document.getElementById('jobCount').textContent = `(${paginationData ? paginationData.total_jobs : jobs.length})`;

    if (jobs.length === 0) {
        jobsList.innerHTML = '<div class="empty-state">No jobs found. Try adjusting your filters or import some jobs!</div>';
        paginationControls.style.display = 'none';
        return;
    }

    jobsList.innerHTML = jobs.map(job => `
        <div class="job-card" onclick="openJobModal(${job.id})">
            <div class="job-card-header">
                <div class="job-card-title">
                    <h3>${job.title}</h3>
                    <p class="company-name">${job.company}</p>
                </div>
                <button class="bookmark-btn ${job.is_bookmarked ? 'bookmarked' : ''}" 
                        onclick="toggleBookmarkCard(event, ${job.id})"
                        title="${job.is_bookmarked ? 'Remove bookmark' : 'Bookmark this job'}">
                    ${job.is_bookmarked ? '★' : '☆'}
                </button>
            </div>

            <div class="job-card-meta">
                <span class="meta-item location">📍 ${job.location}</span>
                <span class="meta-item role">${job.role}</span>
                ${job.salary ? `<span class="meta-item salary">💰 ${job.salary}</span>` : ''}
            </div>

            ${job.description ? `<p class="job-description">${job.description.substring(0, 150)}...</p>` : ''}

            <div class="job-card-footer">
                <small class="posted-date">Posted: ${new Date(job.posted_date).toLocaleDateString()}</small>
                <span class="view-details">View Details →</span>
            </div>
        </div>
    `).join('');

    // Show/hide pagination controls
    // For bookmarked view, only show pagination if there are more than 10 bookmarked jobs
    let shouldShowPagination = paginationData && paginationData.total_pages > 1;
    if (currentView === 'bookmarked') {
        shouldShowPagination = jobs.length > 10;
    }
    
    if (shouldShowPagination) {
        paginationControls.style.display = 'flex';
        document.getElementById('currentPageNum').textContent = paginationData.current_page;
        document.getElementById('totalPagesNum').textContent = paginationData.total_pages;
        
        document.getElementById('prevBtn').disabled = !paginationData.has_prev;
        document.getElementById('nextBtn').disabled = !paginationData.has_next;
    } else {
        paginationControls.style.display = 'none';
    }
}

function nextPage() {
    if (paginationData && paginationData.has_next) {
        currentPage++;
        loadJobs();
        window.scrollTo(0, 0);
    }
}

function previousPage() {
    if (paginationData && paginationData.has_prev) {
        currentPage--;
        loadJobs();
        window.scrollTo(0, 0);
    }
}

async function openJobModal(jobId) {
    currentJobId = jobId;
    try {
        const response = await fetch(`/api/jobs/${jobId}`);
        const job = await response.json();

        document.getElementById('modalTitle').textContent = job.title;
        document.getElementById('modalCompany').textContent = job.company;
        document.getElementById('modalLocation').textContent = job.location;
        document.getElementById('modalRole').textContent = job.role;
        document.getElementById('modalSalary').textContent = job.salary || '-';
        document.getElementById('modalPostedDate').textContent = new Date(job.posted_date).toLocaleDateString();

        if (job.description) {
            document.getElementById('descriptionSection').style.display = 'block';
            document.getElementById('modalDescription').textContent = job.description;
        } else {
            document.getElementById('descriptionSection').style.display = 'none';
        }

        if (job.url) {
            document.getElementById('urlSection').style.display = 'block';
            document.getElementById('modalUrl').href = job.url;
        } else {
            document.getElementById('urlSection').style.display = 'none';
        }

        // Update bookmark button
        const bookmarkBtn = document.getElementById('bookmarkBtn');
        if (job.is_bookmarked) {
            bookmarkBtn.textContent = '✓ You have bookmarked this job';
            bookmarkBtn.classList.add('bookmarked');
        } else {
            bookmarkBtn.textContent = 'Add to bookmarks';
            bookmarkBtn.classList.remove('bookmarked');
        }

        // Show or hide application form
        hideApplicationForm();
        if (job.application) {
            displayApplication(job.application);
        } else {
            document.getElementById('applicationDisplay').innerHTML = `
                <p class="no-application">No application tracked yet</p>
                <button class="edit-btn" id="trackAppBtn">Track Application</button>
            `;
            document.getElementById('trackAppBtn').addEventListener('click', showApplicationForm);
        }

        document.getElementById('jobModal').style.display = 'flex';
    } catch (error) {
        console.error('Error loading job:', error);
    }
}

function displayApplication(app) {
    const appDiv = document.getElementById('applicationDisplay');
    appDiv.innerHTML = `
        <p><strong>Status:</strong> <span class="status-badge ${app.status}">${app.status}</span></p>
        ${app.notes ? `<p><strong>Notes:</strong> ${app.notes}</p>` : ''}
        ${app.applied_date ? `<p><strong>Applied Date:</strong> ${app.applied_date}</p>` : ''}
        <button class="edit-btn" id="trackAppBtn">Update Application</button>
    `;
    document.getElementById('trackAppBtn').addEventListener('click', showApplicationForm);
}

function showApplicationForm() {
    document.getElementById('applicationDisplay').style.display = 'none';
    document.getElementById('applicationForm').style.display = 'block';

    // Fetch current application data if exists
    fetch(`/api/jobs/${currentJobId}`)
        .then(r => r.json())
        .then(job => {
            if (job.application) {
                document.getElementById('appStatus').value = job.application.status;
                document.getElementById('appliedDate').value = job.application.applied_date || '';
                document.getElementById('appNotes').value = job.application.notes || '';
            }
        });
}

function hideApplicationForm() {
    document.getElementById('applicationForm').style.display = 'none';
    document.getElementById('applicationDisplay').style.display = 'block';
}

async function saveApplication() {
    try {
        const response = await fetch('/api/applications', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                job_id: currentJobId,
                status: document.getElementById('appStatus').value,
                notes: document.getElementById('appNotes').value,
                applied_date: document.getElementById('appliedDate').value
            })
        });

        if (response.ok) {
            hideApplicationForm();
            await loadJobs();
            openJobModal(currentJobId);
        }
    } catch (error) {
        console.error('Error saving application:', error);
    }
}

async function toggleBookmarkCard(e, jobId) {
    e.stopPropagation();
    await toggleBookmark(jobId);
}

function showBookmarkRemoveConfirm(jobTitle) {
    return new Promise((resolve) => {
        const modal = document.getElementById('bookmarkConfirmModal');
        const message = document.getElementById('bookmarkConfirmMessage');
        const yesBtn = document.getElementById('bookmarkConfirmYes');
        const noBtn = document.getElementById('bookmarkConfirmNo');

        message.textContent = `Do you want to remove "${jobTitle}" from bookmarks?`;
        modal.style.display = 'flex';

        const cleanup = () => {
            modal.style.display = 'none';
            yesBtn.removeEventListener('click', handleYes);
            noBtn.removeEventListener('click', handleNo);
            modal.removeEventListener('click', handleBackdrop);
            document.removeEventListener('keydown', handleEscape);
        };

        const handleYes = () => {
            cleanup();
            resolve(true);
        };

        const handleNo = () => {
            cleanup();
            resolve(false);
        };

        const handleBackdrop = (e) => {
            if (e.target === modal) {
                cleanup();
                resolve(false);
            }
        };

        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                cleanup();
                resolve(false);
            }
        };

        yesBtn.addEventListener('click', handleYes);
        noBtn.addEventListener('click', handleNo);
        modal.addEventListener('click', handleBackdrop);
        document.addEventListener('keydown', handleEscape);
    });
}

function updateModalBookmarkButton(isBookmarked) {
    const bookmarkBtn = document.getElementById('bookmarkBtn');
    if (!bookmarkBtn) return;

    if (isBookmarked) {
        bookmarkBtn.textContent = '✓ You have bookmarked this job';
        bookmarkBtn.classList.add('bookmarked');
    } else {
        bookmarkBtn.textContent = 'Add to bookmarks';
        bookmarkBtn.classList.remove('bookmarked');
    }
}

function showToast(message, type = 'success') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        // Fallback if template cache did not include the toast container yet.
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-atomic', 'true');
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    // Trigger enter animation after mount
    requestAnimationFrame(() => {
        toast.classList.add('visible');
    });

    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 180);
    }, 3200);
}

async function toggleBookmark(jobId = currentJobId) {
    try {
        const job = allJobs.find(j => j.id === jobId);
        if (!job) {
            await loadJobs();
            return;
        }

        const wasBookmarked = !!job.is_bookmarked;

        if (job.is_bookmarked) {
            // Ask for confirmation before removing bookmark with themed modal
            const shouldRemove = await showBookmarkRemoveConfirm(job.title);
            if (!shouldRemove) {
                return;
            }
            // Immediately update UI before API call
            job.is_bookmarked = false;
            displayJobs();
            if (document.getElementById('jobModal').style.display === 'flex') {
                updateModalBookmarkButton(false);
            }
            // Sync with backend in background
            const response = await fetch(`/api/bookmarks/${jobId}`, { method: 'DELETE' });
            if (!response.ok) {
                throw new Error('Failed to remove bookmark');
            }
            showToast('Bookmark removed', 'info');
        } else {
            // Immediately update UI before API call
            job.is_bookmarked = true;
            displayJobs();
            if (document.getElementById('jobModal').style.display === 'flex') {
                updateModalBookmarkButton(true);
            }
            // Sync with backend in background
            const response = await fetch('/api/bookmarks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_id: jobId })
            });
            if (!response.ok && response.status !== 409) {
                throw new Error('Failed to add bookmark');
            }
            showToast('Job bookmarked', 'success');
        }
    } catch (error) {
        console.error('Error toggling bookmark:', error);
        showToast('Could not update bookmark', 'error');
        // Reload jobs if there was an error to restore correct state
        await loadJobs();
    }
}

async function deleteJob() {
    if (!confirm('Are you sure you want to delete this job?')) return;

    try {
        await fetch(`/api/jobs/${currentJobId}`, { method: 'DELETE' });
        closeModal();
        await loadJobs();
    } catch (error) {
        console.error('Error deleting job:', error);
    }
}

function closeModal() {
    document.getElementById('jobModal').style.display = 'none';
}

function formatElapsedTime(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    if (minutes > 0) {
        return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
}

function formatBreakdownMap(breakdown) {
    if (!breakdown || typeof breakdown !== 'object') {
        return 'None';
    }

    const entries = Object.entries(breakdown);
    if (!entries.length) {
        return 'None';
    }

    return entries
        .map(([name, count]) => `${name}: ${count}`)
        .join(' | ');
}

async function scrapeJobs(source) {
    const scrapeIndeedBtn = document.getElementById('scrapeIndeedBtn');
    const scrapeJobBankBtn = document.getElementById('scrapeJobBankBtn');
    const messageDiv = document.getElementById('scrapeMessage');
    const progressDiv = document.getElementById('scrapeProgress');
    const progressText = progressDiv.querySelector('p');
    const scrapeStartTime = Date.now();
    let elapsedTimer = null;

    const sourceLabel = source === 'jobbank' ? 'JobBank' : 'Indeed';
        const endpoint = source === 'jobbank'
            ? '/api/scrape-jobs/jobbank'
        : '/api/scrape-jobs/indeed';

    if (scrapeIndeedBtn) scrapeIndeedBtn.disabled = true;
    if (scrapeJobBankBtn) scrapeJobBankBtn.disabled = true;
    messageDiv.style.display = 'none';
    progressDiv.style.display = 'flex';

    if (progressText) {
        progressText.textContent = `Scraping ${sourceLabel}... elapsed: 0s`;
        elapsedTimer = setInterval(() => {
            const elapsedSeconds = Math.floor((Date.now() - scrapeStartTime) / 1000);
            progressText.textContent = `Scraping ${sourceLabel}... elapsed: ${formatElapsedTime(elapsedSeconds)}`;
        }, 1000);
    }

    try {
        const response = await fetch(endpoint, {
            method: 'POST'
        });

        const data = await response.json();
        const totalElapsedSeconds = Math.floor((Date.now() - scrapeStartTime) / 1000);
        progressDiv.style.display = 'none';
        messageDiv.style.display = 'block';

        if (response.ok) {
            messageDiv.className = 'scrape-message success';
            const citiesFoundText = Array.isArray(data.cities_found) && data.cities_found.length
                ? data.cities_found.join(', ')
                : 'None';
            const missingCitiesText = Array.isArray(data.missing_cities) && data.missing_cities.length
                ? data.missing_cities.join(', ')
                : 'None';
            const sourceBreakdownText = formatBreakdownMap(data.imported_by_source);
            const cityBreakdownText = formatBreakdownMap(data.imported_by_city);
            messageDiv.innerHTML = `
                <strong>✓ ${sourceLabel} Scrape Complete!</strong>
                <div style="font-size: 0.95em; margin-top: 8px;">
                    Elapsed: ${formatElapsedTime(totalElapsedSeconds)}<br>
                    Cleared (non-bookmarked): ${data.non_bookmarked_cleared || 0}<br>
                    Imported: ${data.imported} jobs<br>
                    Duplicates Skipped: ${data.duplicates_skipped}<br>
                    Blocked (Deleted Jobs): ${data.blocked_deleted || 0}<br>
                    Total Found: ${data.total_found}<br>
                    Cities Found: ${citiesFoundText}<br>
                    Missing Cities: ${missingCitiesText}<br>
                    Jobs by Source: ${sourceBreakdownText}<br>
                    Jobs by City: ${cityBreakdownText}
                </div>
            `;
            await loadJobs();
            setTimeout(() => messageDiv.style.display = 'none', 5000);
        } else {
            messageDiv.className = 'scrape-message error';
            messageDiv.textContent = `✗ Error: ${data.error}`;
        }
    } catch (error) {
        const totalElapsedSeconds = Math.floor((Date.now() - scrapeStartTime) / 1000);
        progressDiv.style.display = 'none';
        messageDiv.style.display = 'block';
        messageDiv.className = 'scrape-message error';
        messageDiv.textContent = `✗ Error scraping jobs after ${formatElapsedTime(totalElapsedSeconds)}. Please try again.`;
        console.error('Scrape error:', error);
    } finally {
        if (elapsedTimer) {
            clearInterval(elapsedTimer);
        }
        if (scrapeIndeedBtn) scrapeIndeedBtn.disabled = false;
        if (scrapeJobBankBtn) scrapeJobBankBtn.disabled = false;
    }
}

function applyFilters() {
    loadJobs();
    updateClearButton();
}

function updateClearButton() {
    const hasFilters = document.getElementById('search').value || 
                      document.getElementById('roleFilter').value || 
                      document.getElementById('locationFilter').value;
    document.getElementById('clearFiltersBtn').style.display = hasFilters ? 'block' : 'none';
}

function clearFilters() {
    document.getElementById('search').value = '';
    document.getElementById('roleFilter').value = '';
    document.getElementById('locationFilter').value = '';
    applyFilters();
}

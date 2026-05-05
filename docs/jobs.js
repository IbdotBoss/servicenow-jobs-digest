// jobs.js - Dynamic job dashboard

document.addEventListener('DOMContentLoaded', function() {
    // State
    let allJobs = [];
    let filteredJobs = [];
    let currentView = 'grid'; // grid or list
    let currentGroupBy = 'none';
    
    // DOM Elements
    const jobsContainer = document.getElementById('jobs-container');
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const clearSearchBtn = document.getElementById('clear-search');
    const locationFilter = document.getElementById('location-filter');
    const companyFilter = document.getElementById('company-filter');
    const sourceFilter = document.getElementById('source-filter');
    const sponsorshipFilter = document.getElementById('sponsorship-filter');
    const remoteFilter = document.getElementById('remote-filter');
    const sortBySelect = document.getElementById('sort-by');
    const groupBySelect = document.getElementById('group-by');
    const gridViewBtn = document.getElementById('grid-view');
    const listViewBtn = document.getElementById('list-view');
    const totalJobsSpan = document.getElementById('total-jobs');
    const sourcesCountSpan = document.getElementById('sources-count');
    const lastUpdatedSpan = document.getElementById('last-updated');
    const jobCountSpan = document.getElementById('job-count');
    
    // Initialize
    init();
    
    // Event Listeners
    searchInput.addEventListener('keyup', debounce(handleSearch, 300));
    searchBtn.addEventListener('click', handleSearch);
    clearSearchBtn.addEventListener('click', clearSearch);
    locationFilter.addEventListener('change', filterJobs);
    companyFilter.addEventListener('change', filterJobs);
    sourceFilter.addEventListener('change', filterJobs);
    sponsorshipFilter.addEventListener('change', filterJobs);
    remoteFilter.addEventListener('change', filterJobs);
    sortBySelect.addEventListener('change', filterJobs);
    groupBySelect.addEventListener('change', handleGroupBy);
    gridViewBtn.addEventListener('click', () => setView('grid'));
    listViewBtn.addEventListener('click', () => setView('list'));
    
    // Initialize the app
    function init() {
        loadJobs();
        populateFilters();
    }
    
    // Load jobs from JSON file
    async function loadJobs() {
        try {
            const response = await fetch('data/jobs.json');
            if (!response.ok) {
                throw new Error('Failed to fetch jobs data');
            }
            allJobs = await response.json();
            filteredJobs = [...allJobs];
            updateStats();
            renderJobs();
        } catch (error) {
            console.error('Error loading jobs:', error);
            jobsContainer.innerHTML = `
                <div class="error">
                    <h3>Unable to load jobs</h3>
                    <p>${error.message}</p>
                    <p>Please try again later or check if the scraper is running.</p>
                </div>
            `;
        }
    }
    
    // Populate filter dropdowns
    function populateFilters() {
        const locations = [...new Set(allJobs.map(job => job.location))].sort();
        const companies = [...new Set(allJobs.map(job => job.company))].sort();
        const sources = [...new Set(allJobs.map(job => job.source))].sort();
        
        // Add locations
        locationFilter.innerHTML = '<option value="all">All Locations</option>';
        locations.forEach(loc => {
            locationFilter.innerHTML += `<option value="${loc}">${loc}</option>`;
        });
        
        // Add companies
        companyFilter.innerHTML = '<option value="all">All Companies</option>';
        companies.forEach(comp => {
            companyFilter.innerHTML += `<option value="${comp}">${comp}</option>`;
        });
        
        // Add sources
        sourceFilter.innerHTML = '<option value="all">All Sources</option>';
        sources.forEach(src => {
            sourceFilter.innerHTML += `<option value="${src}">${src.charAt(0).toUpperCase() + src.slice(1)}</option>`;
        });
        
        // Update sources count
        sourcesCountSpan.textContent = sources.length;
    }
    
    // Handle search
    function handleSearch() {
        const query = searchInput.value.toLowerCase().trim();
        if (!query) {
            filteredJobs = [...allJobs];
        } else {
            filteredJobs = allJobs.filter(job => 
                job.title.toLowerCase().includes(query) ||
                job.company.toLowerCase().includes(query) ||
                job.location.toLowerCase().includes(query) ||
                job.source.toLowerCase().includes(query) ||
                job.tags.some(tag => tag.toLowerCase().includes(query))
            );
        }
        updateStats();
        renderJobs();
    }
    
    // Clear search
    function clearSearch() {
        searchInput.value = '';
        filteredJobs = [...allJobs];
        updateStats();
        renderJobs();
    }
    
    // Filter jobs based on selected criteria
    function filterJobs() {
        const locationVal = locationFilter.value;
        const companyVal = companyFilter.value;
        const sourceVal = sourceFilter.value;
        const sponsorshipVal = sponsorshipFilter.checked;
        const remoteVal = remoteFilter.checked;
        
        filteredJobs = allJobs.filter(job => {
            // Search filter
            const query = searchInput.value.toLowerCase().trim();
            if (query) {
                if (!(job.title.toLowerCase().includes(query) ||
                      job.company.toLowerCase().includes(query) ||
                      job.location.toLowerCase().includes(query) ||
                      job.source.toLowerCase().includes(query) ||
                      job.tags.some(tag => tag.toLowerCase().includes(query)))) {
                    return false;
                }
            }
            
            // Location filter
            if (locationVal !== 'all' && job.location !== locationVal) {
                return false;
            }
            
            // Company filter
            if (companyVal !== 'all' && job.company !== companyVal) {
                return false;
            }
            
            // Source filter
            if (sourceVal !== 'all' && job.source !== sourceVal.toLowerCase()) {
                return false;
            }
            
            // Sponsorship filter
            if (sponsorshipVal && !job.sponsorship_confirmed) {
                return false;
            }
            
            // Remote filter
            if (remoteVal && !job.remote) {
                return false;
            }
            
            return true;
        });
        
        updateStats();
        renderJobs();
    }
    
    // Set view mode (grid or list)
    function setView(view) {
        currentView = view;
        if (view === 'grid') {
            gridViewBtn.classList.add('active');
            listViewBtn.classList.remove('active');
        } else {
            gridViewBtn.classList.remove('active');
            listViewBtn.classList.add('active');
        }
        renderJobs();
    }
    
    // Handle group by
    function handleGroupBy() {
        currentGroupBy = groupBySelect.value;
        renderJobs();
    }
    
    // Sort jobs
    function sortJobs(jobs) {
        const sortBy = sortBySelect.value;
        
        return [...jobs].sort((a, b) => {
            switch(sortBy) {
                case 'date-desc':
                    return new Date(b.date) - new Date(a.date);
                case 'date-asc':
                    return new Date(a.date) - new Date(b.date);
                case 'company':
                    return a.company.localeCompare(b.company);
                case 'location':
                    return a.location.localeCompare(b.location);
                case 'source':
                    return a.source.localeCompare(b.source);
                default:
                    return 0;
            }
        });
    }
    
    // Render jobs to the DOM
    function renderJobs() {
        if (filteredJobs.length === 0) {
            jobsContainer.innerHTML = `
                <div class="no-jobs">
                    <h3>No jobs found</h3>
                    <p>Try adjusting your filters or search terms.</p>
                </div>
            `;
            return;
        }
        
        const sortedJobs = sortJobs(filteredJobs);
        
        if (currentGroupBy !== 'none') {
            renderGroupedJobs(sortedJobs);
        } else if (currentView === 'grid') {
            renderGrid(jobsContainer, sortedJobs);
        } else {
            renderList(jobsContainer, sortedJobs);
        }
    }
    
    // Render jobs in grid view
    function renderGrid(container, jobs) {
        container.innerHTML = `
            <div class="job-grid">
                ${jobs.map(job => createJobCard(job)).join('')}
            </div>
        `;
    }
    
    // Render jobs in list view
    function renderList(container, jobs) {
        container.innerHTML = `
            <div class="job-list">
                ${jobs.map(job => createJobItem(job)).join('')}
            </div>
        `;
    }
    
    // Render grouped jobs
    function renderGroupedJobs(jobs) {
        const groups = {};
        const groupBy = currentGroupBy;
        
        // Group jobs
        jobs.forEach(job => {
            const key = groupBy === 'tags' 
                ? job.tags.join(', ') 
                : groupBy === 'company' ? job.company 
                : groupBy === 'location' ? job.location 
                : job.source;
            
            if (!groups[key]) {
                groups[key] = [];
            }
            groups[key].push(job);
        });
        
        // Sort group keys
        const sortedKeys = Object.keys(groups).sort();
        
        // Render groups
        let html = '';
        sortedKeys.forEach(key => {
            const groupJobs = groups[key];
            html += `
                <div class="grouped-section">
                    <div class="group-toggle" onclick="toggleGroup(this)">
                        <h3>${key} (${groupJobs.length})</h3>
                        <span>▼</span>
                    </div>
                    <div class="group-content open">
                        ${currentView === 'grid' 
                            ? `<div class="job-grid">${groupJobs.map(job => createJobCard(job)).join('')}</div>`
                            : `<div class="job-list">${groupJobs.map(job => createJobItem(job)).join('')}</div>`
                        }
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    // Create job card HTML (grid view)
    function createJobCard(job) {
        const tagsHtml = job.tags.map(tag => 
            `<span class="tag">${tag}</span>`
        ).join('');
        
        const sponsorBadge = job.sponsorship_confirmed 
            ? `<span class="tag sponsor-badge">✓ Sponsorship</span>` 
            : '';
        
        return `
            <div class="job-card">
                <h3 class="job-title">
                    <a href="${job.link}" target="_blank">${job.title}</a>
                </h3>
                <div class="job-company">${job.company}</div>
                <div class="job-location">${job.location}</div>
                <div class="job-meta">
                    ${tagsHtml}
                    ${sponsorBadge}
                    <span class="source">${job.source.replace('_', ' ').charAt(0).toUpperCase() + job.source.slice(1)}</span>
                </div>
            </div>
        `;
    }
    
    // Create job item HTML (list view)
    function createJobItem(job) {
        const tagsHtml = job.tags.map(tag => 
            `<span class="tag">${tag}</span>`
        ).join('');
        
        const sponsorBadge = job.sponsorship_confirmed 
            ? `<span class="tag sponsor-badge">✓ Sponsorship</span>` 
            : '';
        
        return `
            <div class="job-item">
                <h3 class="job-title">
                    <a href="${job.link}" target="_blank">${job.title}</a>
                </h3>
                <div class="job-details">
                    <div class="detail">
                        <strong>Company:</strong> ${job.company}
                    </div>
                    <div class="detail">
                        <strong>Location:</strong> ${job.location}
                    </div>
                    <div class="detail">
                        <strong>Source:</strong> ${job.source.replace('_', ' ').charAt(0).toUpperCase() + job.source.slice(1)}
                    </div>
                </div>
                <div class="tags">
                    ${tagsHtml}
                    ${sponsorBadge}
                </div>
            </div>
        `;
    }
    
    // Toggle group visibility
    window.toggleGroup = function(element) {
        const content = element.nextElementSibling;
        content.classList.toggle('open');
        const arrow = element.querySelector('span');
        arrow.textContent = content.classList.contains('open') ? '▲' : '▼';
    }
    
    // Update statistics
    function updateStats() {
        totalJobsSpan.textContent = allJobs.length;
        jobCountSpan.textContent = filteredJobs.length;
        lastUpdatedSpan.textContent = new Date().toLocaleDateString('en-GB', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    }
    
    // Utility: Debounce function
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
});
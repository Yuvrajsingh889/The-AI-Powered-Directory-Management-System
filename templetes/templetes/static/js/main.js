// Main JavaScript for the AI Directory Manager application

document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const scanForm = document.getElementById('scan-form');
    const directoryInput = document.getElementById('directory-input');
    const scanBtn = document.getElementById('scan-btn');
    const scanResults = document.getElementById('scan-results');
    const loadingSpinner = document.getElementById('loading-spinner');
    const errorAlert = document.getElementById('error-alert');
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const categoryFilter = document.getElementById('category-filter');
    const filesList = document.getElementById('files-list');
    const statsContainer = document.getElementById('stats-container');
    const visualizeBtn = document.getElementById('visualize-btn');
    
    // Current scan data
    let currentScanData = [];
    
    // Initialize tooltips and popovers if using Bootstrap
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        
        const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
        const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    }
    
    // Handle directory scan submission
    if (scanForm) {
        scanForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const directoryPath = directoryInput.value.trim();
            if (!directoryPath) {
                showError('Please enter a directory path');
                return;
            }
            
            try {
                // Show loading spinner
                showLoading(true);
                
                // Clear previous results
                clearResults();
                
                // Send scan request to backend
                const response = await fetch('/api/scan', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ path: directoryPath })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to scan directory');
                }
                
                // Store scan data
                currentScanData = data.files;
                
                // Display scan results summary
                displayScanSummary(data);
                
                // Display file list
                displayFilesList(data.files);
                
                // Update category filter options
                updateCategoryFilter(data.files);
                
                // Enable visualization button
                if (visualizeBtn) {
                    visualizeBtn.disabled = false;
                }
                
            } catch (error) {
                showError(error.message || 'An error occurred during scanning');
                console.error('Scan error:', error);
            } finally {
                showLoading(false);
            }
        });
    }
    
    // Handle file search
    if (searchForm) {
        searchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const query = searchInput.value.trim();
            const selectedCategories = Array.from(categoryFilter.selectedOptions).map(option => option.value);
            
            if (!currentScanData.length) {
                showError('No scan data available. Please scan a directory first.');
                return;
            }
            
            try {
                showLoading(true);
                
                // Send search request to backend
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        query: query,
                        filters: {
                            categories: selectedCategories.length > 0 ? selectedCategories : null
                        }
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to search files');
                }
                
                // Display search results
                displayFilesList(data.results);
                
            } catch (error) {
                showError(error.message || 'An error occurred during search');
                console.error('Search error:', error);
            } finally {
                showLoading(false);
            }
        });
    }
    
    // Handle visualization button click
    if (visualizeBtn) {
        visualizeBtn.addEventListener('click', async () => {
            try {
                showLoading(true);
                
                // Fetch visualization data from backend
                const response = await fetch('/api/visualize');
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to generate visualization');
                }
                
                // Initialize visualizations
                initializeVisualizations(data.visualization);
                
                // Show visualization section
                document.getElementById('visualization-section').classList.remove('d-none');
                
                // Scroll to visualizations
                document.getElementById('visualization-section').scrollIntoView({
                    behavior: 'smooth'
                });
                
            } catch (error) {
                showError(error.message || 'An error occurred while generating visualizations');
                console.error('Visualization error:', error);
            } finally {
                showLoading(false);
            }
        });
    }
    
    // Function to show/hide loading spinner
    function showLoading(isLoading) {
        if (loadingSpinner) {
            loadingSpinner.style.display = isLoading ? 'block' : 'none';
        }
    }
    
    // Function to display error message
    function showError(message) {
        if (errorAlert) {
            errorAlert.textContent = message;
            errorAlert.classList.remove('d-none');
            
            // Auto-hide error after 5 seconds
            setTimeout(() => {
                errorAlert.classList.add('d-none');
            }, 5000);
        }
    }
    
    // Function to clear previous results
    function clearResults() {
        if (scanResults) {
            scanResults.classList.add('d-none');
        }
        
        if (filesList) {
            filesList.innerHTML = '';
        }
        
        if (statsContainer) {
            statsContainer.innerHTML = '';
        }
        
        // Hide visualization section
        const visualizationSection = document.getElementById('visualization-section');
        if (visualizationSection) {
            visualizationSection.classList.add('d-none');
        }
        
        // Clear any error messages
        if (errorAlert) {
            errorAlert.classList.add('d-none');
        }
    }
    
    // Function to display scan summary
    function displayScanSummary(data) {
        if (!scanResults) return;
        
        // Calculate statistics
        const totalFiles = data.files.length;
        const totalSize = data.files.reduce((sum, file) => sum + file.size_bytes, 0);
        const formattedSize = formatFileSize(totalSize);
        
        // Count files by category
        const categoryCount = {};
        data.files.forEach(file => {
            const category = file.category || 'Uncategorized';
            categoryCount[category] = (categoryCount[category] || 0) + 1;
        });
        
        // Build summary HTML
        let summaryHtml = `
            <div class="card mb-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">Scan Summary</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            <div class="d-flex align-items-center mb-3">
                                <i class="fas fa-file me-2 text-primary"></i>
                                <div>
                                    <h6 class="mb-0">Total Files</h6>
                                    <h4 class="mb-0">${totalFiles}</h4>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="d-flex align-items-center mb-3">
                                <i class="fas fa-database me-2 text-info"></i>
                                <div>
                                    <h6 class="mb-0">Total Size</h6>
                                    <h4 class="mb-0">${formattedSize}</h4>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="d-flex align-items-center mb-3">
                                <i class="fas fa-folder me-2 text-warning"></i>
                                <div>
                                    <h6 class="mb-0">Categories</h6>
                                    <h4 class="mb-0">${Object.keys(categoryCount).length}</h4>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Display category breakdown
        summaryHtml += `
            <div class="card mb-4">
                <div class="card-header bg-info text-white">
                    <h5 class="mb-0">Category Breakdown</h5>
                </div>
                <div class="card-body">
                    <div class="row">
        `;
        
        // Sort categories by count
        const sortedCategories = Object.entries(categoryCount)
            .sort((a, b) => b[1] - a[1]);
        
        sortedCategories.forEach(([category, count]) => {
            const percentage = ((count / totalFiles) * 100).toFixed(1);
            summaryHtml += `
                <div class="col-md-6 col-lg-4 mb-3">
                    <div class="d-flex justify-content-between">
                        <span>${category}</span>
                        <span class="badge bg-primary rounded-pill">${count}</span>
                    </div>
                    <div class="progress mt-1" style="height: 10px;">
                        <div class="progress-bar" role="progressbar" style="width: ${percentage}%;" 
                            aria-valuenow="${percentage}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
            `;
        });
        
        summaryHtml += `
                    </div>
                </div>
            </div>
        `;
        
        // Update the summary container
        statsContainer.innerHTML = summaryHtml;
        scanResults.classList.remove('d-none');
    }
    
    // Function to display files list
    function displayFilesList(files) {
        if (!filesList) return;
        
        if (files.length === 0) {
            filesList.innerHTML = '<div class="alert alert-info">No files found matching your criteria.</div>';
            return;
        }
        
        let html = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Category</th>
                            <th>Size</th>
                            <th>Modified</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        files.forEach(file => {
            const modifiedDate = new Date(file.modified).toLocaleString();
            const fileIcon = getFileIcon(file.extension, file.category);
            
            html += `
                <tr>
                    <td>
                        <div class="d-flex align-items-center">
                            <span class="me-2">${fileIcon}</span>
                            <span class="text-truncate" style="max-width: 250px;" 
                                title="${file.path}">${file.name}</span>
                        </div>
                    </td>
                    <td><span class="badge bg-secondary">${file.category || 'Unknown'}</span></td>
                    <td>${file.size_display}</td>
                    <td>${modifiedDate}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-info me-1" 
                            onclick="showFileDetails('${encodeURIComponent(JSON.stringify(file))}')">
                            <i class="fas fa-info-circle"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        filesList.innerHTML = html;
    }
    
    // Function to update category filter options
    function updateCategoryFilter(files) {
        if (!categoryFilter) return;
        
        // Get unique categories
        const categories = [...new Set(files.map(file => file.category || 'Uncategorized'))];
        categories.sort();
        
        // Clear existing options
        categoryFilter.innerHTML = '';
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'All Categories';
        categoryFilter.appendChild(defaultOption);
        
        // Add category options
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categoryFilter.appendChild(option);
        });
    }
    
    // Utility function to format file size
    function formatFileSize(bytes) {
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let unitIndex = 0;
        let size = bytes;
        
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        
        return `${size.toFixed(2)} ${units[unitIndex]}`;
    }
    
    // Function to get appropriate icon for file type
    function getFileIcon(extension, category) {
        // Default icon
        let iconClass = 'fas fa-file text-secondary';
        
        // Icons based on category
        const categoryIcons = {
            'Documents': 'fas fa-file-alt text-primary',
            'Spreadsheets': 'fas fa-file-excel text-success',
            'Presentations': 'fas fa-file-powerpoint text-warning',
            'Images': 'fas fa-file-image text-info',
            'Audio': 'fas fa-file-audio text-danger',
            'Video': 'fas fa-file-video text-danger',
            'Archives': 'fas fa-file-archive text-secondary',
            'Code': 'fas fa-file-code text-primary',
            'Executables': 'fas fa-cog text-danger',
            'System': 'fas fa-cogs text-warning',
            'Configuration': 'fas fa-wrench text-info',
            'Database': 'fas fa-database text-success',
            'Backup': 'fas fa-save text-warning',
            'Temporary': 'fas fa-clock text-secondary',
            'Project': 'fas fa-project-diagram text-primary',
            'Fonts': 'fas fa-font text-dark'
        };
        
        // Use category-based icon if available
        if (category && categoryIcons[category]) {
            iconClass = categoryIcons[category];
        } else {
            // Fallback to extension-based icons for common types
            const extensionIcons = {
                'pdf': 'fas fa-file-pdf text-danger',
                'doc': 'fas fa-file-word text-primary',
                'docx': 'fas fa-file-word text-primary',
                'xls': 'fas fa-file-excel text-success',
                'xlsx': 'fas fa-file-excel text-success',
                'ppt': 'fas fa-file-powerpoint text-warning',
                'pptx': 'fas fa-file-powerpoint text-warning',
                'jpg': 'fas fa-file-image text-info',
                'jpeg': 'fas fa-file-image text-info',
                'png': 'fas fa-file-image text-info',
                'gif': 'fas fa-file-image text-info',
                'mp3': 'fas fa-file-audio text-danger',
                'wav': 'fas fa-file-audio text-danger',
                'mp4': 'fas fa-file-video text-danger',
                'zip': 'fas fa-file-archive text-secondary',
                'rar': 'fas fa-file-archive text-secondary',
                'py': 'fab fa-python text-primary',
                'js': 'fab fa-js text-warning',
                'html': 'fab fa-html5 text-danger',
                'css': 'fab fa-css3 text-primary',
                'json': 'fas fa-code text-success',
                'xml': 'fas fa-code text-success',
                'txt': 'fas fa-file-alt text-secondary',
                'md': 'fas fa-file-alt text-secondary'
            };
            
            if (extension && extensionIcons[extension.toLowerCase()]) {
                iconClass = extensionIcons[extension.toLowerCase()];
            }
        }
        
        return `<i class="${iconClass}"></i>`;
    }
});

// Function to show file details (must be global for onclick handler)
function showFileDetails(fileDataEncoded) {
    const fileData = JSON.parse(decodeURIComponent(fileDataEncoded));
    
    // Create modal dynamically if it doesn't exist
    let fileModal = document.getElementById('file-details-modal');
    if (!fileModal) {
        const modalHtml = `
            <div class="modal fade" id="file-details-modal" tabindex="-1" aria-labelledby="fileDetailsModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="fileDetailsModalLabel">File Details</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" id="file-details-content">
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer.firstChild);
        
        fileModal = document.getElementById('file-details-modal');
    }
    
    // Format dates
    const createdDate = new Date(fileData.created).toLocaleString();
    const modifiedDate = new Date(fileData.modified).toLocaleString();
    const accessedDate = new Date(fileData.accessed).toLocaleString();
    
    // Prepare modal content
    const contentDiv = document.getElementById('file-details-content');
    contentDiv.innerHTML = `
        <div class="row">
            <div class="col-md-12 mb-3">
                <h5 class="text-truncate">${fileData.name}</h5>
                <p class="text-muted text-truncate">${fileData.path}</p>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <table class="table">
                    <tr>
                        <th>Category:</th>
                        <td><span class="badge bg-secondary">${fileData.category || 'Unknown'}</span></td>
                    </tr>
                    <tr>
                        <th>Extension:</th>
                        <td>${fileData.extension || 'None'}</td>
                    </tr>
                    <tr>
                        <th>Size:</th>
                        <td>${fileData.size_display} (${fileData.size_bytes} bytes)</td>
                    </tr>
                    <tr>
                        <th>MIME Type:</th>
                        <td>${fileData.mime_type || 'Unknown'}</td>
                    </tr>
                </table>
            </div>
            
            <div class="col-md-6">
                <table class="table">
                    <tr>
                        <th>Created:</th>
                        <td>${createdDate}</td>
                    </tr>
                    <tr>
                        <th>Modified:</th>
                        <td>${modifiedDate}</td>
                    </tr>
                    <tr>
                        <th>Accessed:</th>
                        <td>${accessedDate}</td>
                    </tr>
                    <tr>
                        <th>Permissions:</th>
                        <td>
                            ${fileData.is_readable ? '<span class="badge bg-success">Read</span> ' : ''}
                            ${fileData.is_writable ? '<span class="badge bg-warning">Write</span> ' : ''}
                            ${fileData.is_executable ? '<span class="badge bg-danger">Execute</span>' : ''}
                        </td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="row mt-3">
            <div class="col-12">
                <div class="card bg-light">
                    <div class="card-body">
                        <h6 class="card-title">File Path</h6>
                        <div class="d-flex align-items-center">
                            ${fileData.directory}/<strong>${fileData.name}</strong>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Show the modal
    const modal = new bootstrap.Modal(fileModal);
    modal.show();
}

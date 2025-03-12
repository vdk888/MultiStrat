/**
 * Dashboard JavaScript for Portfolio Management System
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips and popovers from Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    
    // Load dashboard data
    loadDashboardData();
    
    // Set up refresh interval (every 5 minutes)
    setInterval(loadDashboardData, 5 * 60 * 1000);
    
    // Set up event listeners
    setupEventListeners();
});

/**
 * Load main dashboard data
 */
function loadDashboardData() {
    // Get portfolio summary
    fetch('/api/v1/portfolios')
        .then(response => response.json())
        .then(data => {
            updatePortfolioSummary(data);
        })
        .catch(error => {
            console.error('Error fetching portfolio data:', error);
            showErrorMessage('Failed to load portfolio data. Please try again later.');
        });
    
    // Get system health status
    fetch('/api/v1/health')
        .then(response => response.json())
        .then(data => {
            updateHealthStatus(data);
        })
        .catch(error => {
            console.error('Error fetching health status:', error);
        });
    
    // Load performance charts if we're on the dashboard
    if (document.getElementById('performance-chart')) {
        loadPerformanceCharts();
    }
}

/**
 * Update portfolio summary section
 */
function updatePortfolioSummary(portfolios) {
    const summaryContainer = document.getElementById('portfolio-summary');
    if (!summaryContainer) return;
    
    // Clear existing content
    summaryContainer.innerHTML = '';
    
    if (!portfolios || portfolios.length === 0) {
        summaryContainer.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No portfolios found. Create a portfolio to get started.
            </div>
        `;
        return;
    }
    
    // Calculate total portfolio value
    let totalValue = 0;
    portfolios.forEach(portfolio => {
        if (portfolio.current_value) {
            totalValue += portfolio.current_value;
        }
    });
    
    // Add total value card
    const totalValueHtml = `
        <div class="col-xl-4 col-md-6 mb-4">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body">
                    <h5 class="card-title text-muted mb-0">Total Portfolio Value</h5>
                    <div class="d-flex align-items-center mt-3">
                        <div class="text-primary display-4 me-3">$${formatNumber(totalValue, 2)}</div>
                        <div class="text-success">
                            <i class="fas fa-chart-line me-1"></i> ${portfolios.length} portfolios
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Create HTML for each portfolio
    const portfolioItems = portfolios.map(portfolio => {
        return `
            <div class="col-xl-4 col-md-6 mb-4">
                <div class="card border-0 shadow-sm h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-center justify-content-between mb-3">
                            <h5 class="card-title mb-0">${portfolio.name}</h5>
                            <span class="badge ${portfolio.is_active ? 'bg-success' : 'bg-secondary'}">
                                ${portfolio.is_active ? 'Active' : 'Inactive'}
                            </span>
                        </div>
                        <div class="d-flex align-items-center mt-3">
                            <div class="text-primary fw-bold fs-4 me-3">$${formatNumber(portfolio.current_value, 2)}</div>
                        </div>
                        <div class="text-muted small mt-3">
                            Risk Tolerance: ${portfolio.risk_tolerance * 100}%
                        </div>
                        <div class="mt-4">
                            <a href="/portfolios/${portfolio.id}" class="btn btn-sm btn-outline-primary">
                                <i class="fas fa-eye me-1"></i> View
                            </a>
                            <a href="/portfolios/${portfolio.id}/allocations" class="btn btn-sm btn-outline-secondary">
                                <i class="fas fa-sliders-h me-1"></i> Allocations
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    // Add content to container
    summaryContainer.innerHTML = totalValueHtml + portfolioItems;
}

/**
 * Update system health status
 */
function updateHealthStatus(healthData) {
    const statusElement = document.getElementById('system-status');
    if (!statusElement) return;
    
    if (healthData.status === 'ok') {
        statusElement.innerHTML = `
            <span class="badge bg-success">
                <i class="fas fa-check-circle me-1"></i> System Healthy
            </span>
        `;
    } else {
        statusElement.innerHTML = `
            <span class="badge bg-danger">
                <i class="fas fa-exclamation-circle me-1"></i> System Error
            </span>
        `;
    }
}

/**
 * Load and render performance charts
 */
function loadPerformanceCharts() {
    // Get active portfolios for performance data
    fetch('/api/v1/portfolios?is_active=true')
        .then(response => response.json())
        .then(portfolios => {
            if (!portfolios || portfolios.length === 0) return;
            
            // Get performance data for first portfolio (or a specific one)
            const portfolioId = getSelectedPortfolioId() || portfolios[0].id;
            
            fetchPerformanceData(portfolioId);
        })
        .catch(error => {
            console.error('Error fetching portfolios for charts:', error);
        });
}

/**
 * Fetch performance data for a specific portfolio
 */
function fetchPerformanceData(portfolioId) {
    fetch(`/api/v1/portfolios/${portfolioId}/performance?limit=30`)
        .then(response => response.json())
        .then(data => {
            renderPerformanceCharts(data);
        })
        .catch(error => {
            console.error('Error fetching performance data:', error);
        });
}

/**
 * Render performance charts with the data
 */
function renderPerformanceCharts(performanceData) {
    if (!performanceData || performanceData.length === 0) {
        document.getElementById('performance-chart').innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No performance data available.
            </div>
        `;
        return;
    }
    
    // Prepare data for charts
    const timestamps = performanceData.map(p => new Date(p.timestamp));
    const totalReturns = performanceData.map(p => p.total_return);
    const sharpeRatios = performanceData.map(p => p.sharpe_ratio);
    const drawdowns = performanceData.map(p => p.max_drawdown);
    
    // Sort by timestamp ascending
    const indices = Array.from(timestamps.keys()).sort((a, b) => timestamps[a] - timestamps[b]);
    
    const sortedTimestamps = indices.map(i => timestamps[i]);
    const sortedReturns = indices.map(i => totalReturns[i]);
    const sortedSharpe = indices.map(i => sharpeRatios[i]);
    const sortedDrawdowns = indices.map(i => drawdowns[i]);
    
    // Render returns chart
    const returnsChart = new Chart(
        document.getElementById('returns-chart'),
        {
            type: 'line',
            data: {
                labels: sortedTimestamps,
                datasets: [{
                    label: 'Total Return (%)',
                    data: sortedReturns,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderWidth: 2,
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day'
                        }
                    },
                    y: {
                        beginAtZero: false
                    }
                }
            }
        }
    );
    
    // Render Sharpe ratio chart
    const sharpeChart = new Chart(
        document.getElementById('sharpe-chart'),
        {
            type: 'line',
            data: {
                labels: sortedTimestamps,
                datasets: [{
                    label: 'Sharpe Ratio',
                    data: sortedSharpe,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderWidth: 2,
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day'
                        }
                    },
                    y: {
                        beginAtZero: false
                    }
                }
            }
        }
    );
    
    // Render drawdown chart
    const drawdownChart = new Chart(
        document.getElementById('drawdown-chart'),
        {
            type: 'line',
            data: {
                labels: sortedTimestamps,
                datasets: [{
                    label: 'Max Drawdown (%)',
                    data: sortedDrawdowns,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderWidth: 2,
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day'
                        }
                    },
                    y: {
                        beginAtZero: true
                    }
                }
            }
        }
    );
}

/**
 * Get the currently selected portfolio ID from the UI
 */
function getSelectedPortfolioId() {
    const portfolioSelector = document.getElementById('portfolio-selector');
    return portfolioSelector ? portfolioSelector.value : null;
}

/**
 * Set up UI event listeners
 */
function setupEventListeners() {
    // Portfolio selector change
    const portfolioSelector = document.getElementById('portfolio-selector');
    if (portfolioSelector) {
        portfolioSelector.addEventListener('change', function() {
            const portfolioId = this.value;
            fetchPerformanceData(portfolioId);
        });
    }
    
    // Refresh button
    const refreshButton = document.getElementById('refresh-data');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            loadDashboardData();
        });
    }
    
    // Portfolio creation form
    const createPortfolioForm = document.getElementById('create-portfolio-form');
    if (createPortfolioForm) {
        createPortfolioForm.addEventListener('submit', function(e) {
            e.preventDefault();
            createPortfolio(this);
        });
    }
    
    // Handle optimization form submissions
    const optimizationForm = document.getElementById('optimization-form');
    if (optimizationForm) {
        optimizationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            startOptimization(this);
        });
    }
}

/**
 * Create a new portfolio via API
 */
function createPortfolio(form) {
    const formData = new FormData(form);
    const portfolioData = {
        name: formData.get('name'),
        description: formData.get('description') || '',
        initial_capital: parseFloat(formData.get('initial_capital')) || 10000,
        risk_tolerance: parseFloat(formData.get('risk_tolerance')) / 100 || 0.5
    };
    
    fetch('/api/v1/portfolios', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(portfolioData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.detail || 'Failed to create portfolio');
            });
        }
        return response.json();
    })
    .then(data => {
        showSuccessMessage('Portfolio created successfully!');
        // Reset form
        form.reset();
        // Close modal if open
        const modal = bootstrap.Modal.getInstance(document.getElementById('create-portfolio-modal'));
        if (modal) {
            modal.hide();
        }
        // Refresh data
        loadDashboardData();
    })
    .catch(error => {
        console.error('Error creating portfolio:', error);
        showErrorMessage(error.message);
    });
}

/**
 * Start an optimization task
 */
function startOptimization(form) {
    const formData = new FormData(form);
    const optimizationData = {
        strategy_id: parseInt(formData.get('strategy_id')),
        asset_ids: Array.from(form.querySelectorAll('input[name="asset_ids"]:checked')).map(cb => parseInt(cb.value)),
        objective: formData.get('objective'),
        days: parseInt(formData.get('days')) || 30
    };
    
    if (optimizationData.asset_ids.length === 0) {
        showErrorMessage('Please select at least one asset to optimize');
        return;
    }
    
    // Show loading indicator
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Optimizing...';
    
    fetch('/api/v1/optimization/optimize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(optimizationData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.detail || 'Failed to start optimization');
            });
        }
        return response.json();
    })
    .then(data => {
        showSuccessMessage('Optimization started successfully! This may take a few minutes.');
        // Start polling for status updates
        pollOptimizationStatus(data.task_id);
    })
    .catch(error => {
        console.error('Error starting optimization:', error);
        showErrorMessage(error.message);
        // Reset button
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Start Optimization';
    });
}

/**
 * Poll for optimization status updates
 */
function pollOptimizationStatus(taskId) {
    const statusElement = document.getElementById('optimization-status');
    if (!statusElement) return;
    
    statusElement.innerHTML = `
        <div class="alert alert-info">
            <div class="d-flex align-items-center">
                <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                <span>Optimization in progress... (0%)</span>
            </div>
            <div class="progress mt-2" style="height: 5px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 0%"></div>
            </div>
        </div>
    `;
    
    // Poll every 2 seconds
    const intervalId = setInterval(() => {
        fetch(`/api/v1/optimization/status/${taskId}`)
            .then(response => response.json())
            .then(data => {
                // Update progress display
                const progressPercent = Math.round(data.progress * 100);
                statusElement.innerHTML = `
                    <div class="alert ${data.status === 'completed' ? 'alert-success' : data.status === 'failed' ? 'alert-danger' : 'alert-info'}">
                        <div class="d-flex align-items-center">
                            ${data.status === 'completed' ? 
                              '<i class="fas fa-check-circle me-2"></i>' : 
                              data.status === 'failed' ? 
                              '<i class="fas fa-exclamation-circle me-2"></i>' : 
                              '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>'}
                            <span>${data.status === 'completed' ? 
                                  'Optimization completed successfully!' : 
                                  data.status === 'failed' ? 
                                  `Optimization failed: ${data.error}` : 
                                  `Optimization in progress... (${progressPercent}%)`}</span>
                        </div>
                        ${data.status === 'running' ? `
                        <div class="progress mt-2" style="height: 5px;">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: ${progressPercent}%"></div>
                        </div>` : ''}
                    </div>
                `;
                
                // Stop polling when completed or failed
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(intervalId);
                    
                    // Reset form button
                    const form = document.getElementById('optimization-form');
                    if (form) {
                        const submitBtn = form.querySelector('button[type="submit"]');
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = 'Start Optimization';
                    }
                    
                    // If completed, fetch latest results
                    if (data.status === 'completed') {
                        fetch(`/api/v1/optimization/latest/${data.strategy_id}`)
                            .then(response => response.json())
                            .then(result => {
                                displayOptimizationResults(result);
                            })
                            .catch(error => {
                                console.error('Error fetching optimization results:', error);
                            });
                    }
                }
            })
            .catch(error => {
                console.error('Error polling optimization status:', error);
                clearInterval(intervalId);
                statusElement.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Error checking optimization status. Please try again later.
                    </div>
                `;
                
                // Reset form button
                const form = document.getElementById('optimization-form');
                if (form) {
                    const submitBtn = form.querySelector('button[type="submit"]');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Start Optimization';
                }
            });
    }, 2000);
}

/**
 * Display optimization results
 */
function displayOptimizationResults(results) {
    const resultsContainer = document.getElementById('optimization-results');
    if (!resultsContainer) return;
    
    // Format parameters for display
    const formattedParams = Object.entries(results.parameters)
        .filter(([key, value]) => typeof value !== 'object')  // Skip complex objects like weights
        .map(([key, value]) => `<tr><td>${formatParamName(key)}</td><td>${formatParamValue(value)}</td></tr>`)
        .join('');
    
    // Display metrics
    resultsContainer.innerHTML = `
        <div class="card border-0 shadow-sm mt-4">
            <div class="card-header bg-transparent">
                <h5 class="card-title mb-0">Optimization Results</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h6>Performance Metrics</h6>
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <tbody>
                                    <tr>
                                        <td>Sharpe Ratio</td>
                                        <td>${formatNumber(results.metrics.sharpe_ratio, 2)}</td>
                                    </tr>
                                    <tr>
                                        <td>Total Return</td>
                                        <td>${formatNumber(results.metrics.total_return, 2)}%</td>
                                    </tr>
                                    <tr>
                                        <td>Max Drawdown</td>
                                        <td>${formatNumber(results.metrics.max_drawdown, 2)}%</td>
                                    </tr>
                                    <tr>
                                        <td>Win Rate</td>
                                        <td>${formatNumber(results.metrics.win_rate, 2)}%</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6>Optimized Parameters</h6>
                        <div class="table-responsive" style="max-height: 200px; overflow-y: auto;">
                            <table class="table table-sm">
                                <tbody>
                                    ${formattedParams}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Format parameter names for display
 */
function formatParamName(name) {
    return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Format parameter values for display
 */
function formatParamValue(value) {
    if (typeof value === 'number') {
        return value % 1 === 0 ? value : formatNumber(value, 2);
    }
    return value;
}

/**
 * Show success message
 */
function showSuccessMessage(message) {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    const alertElement = document.createElement('div');
    alertElement.className = 'alert alert-success alert-dismissible fade show';
    alertElement.innerHTML = `
        <i class="fas fa-check-circle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertsContainer.appendChild(alertElement);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertElement.classList.remove('show');
        setTimeout(() => {
            alertElement.remove();
        }, 150);
    }, 5000);
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    const alertElement = document.createElement('div');
    alertElement.className = 'alert alert-danger alert-dismissible fade show';
    alertElement.innerHTML = `
        <i class="fas fa-exclamation-circle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertsContainer.appendChild(alertElement);
    
    // Auto-dismiss after 8 seconds
    setTimeout(() => {
        alertElement.classList.remove('show');
        setTimeout(() => {
            alertElement.remove();
        }, 150);
    }, 8000);
}

/**
 * Format a number with commas and specified decimal places
 */
function formatNumber(value, decimals = 0) {
    if (value === null || value === undefined) return '-';
    return parseFloat(value).toLocaleString('en-US', { 
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

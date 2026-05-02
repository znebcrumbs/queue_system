// Chart.js Configuration and Helper Functions

const ChartConfig = {
    // Default options for all charts
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: true,
                position: 'bottom',
                labels: {
                    padding: 20,
                    font: { size: 12, weight: '500' },
                    color: '#333'
                }
            }
        }
    },

    // Color palette
    colors: {
        primary: '#0066cc',
        success: '#28a745',
        warning: '#ffc107',
        danger: '#dc3545',
        info: '#17a2b8',
        light: '#f8f9fa',
        dark: '#343a40',
        // Status colors
        pending: '#ffc107',
        waiting: '#17a2b8',
        completed: '#28a745',
        inProgress: '#007bff',
        cancelled: '#dc3545'
    },

    // Create queue status pie chart
    createQueueStatusChart: function(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels || ['Waiting', 'In Progress', 'Completed'],
                datasets: [{
                    data: data.values || [0, 0, 0],
                    backgroundColor: [
                        this.colors.waiting,
                        this.colors.inProgress,
                        this.colors.success
                    ],
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed + ' tickets';
                            }
                        }
                    }
                }
            }
        });
    },

    // Create bar chart for department workload
    createDepartmentBarChart: function(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Tickets',
                    data: data.values || [],
                    backgroundColor: this.colors.primary,
                    borderColor: this.colors.primary,
                    borderWidth: 1,
                    borderRadius: 5
                }]
            },
            options: {
                ...this.defaultOptions,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: '#e9ecef' }
                    },
                    y: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: { display: false }
                }
            }
        });
    },

    // Create line chart for trends
    createTrendLineChart: function(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: data.label || 'Trend',
                    data: data.values || [],
                    borderColor: this.colors.primary,
                    backgroundColor: 'rgba(0, 102, 204, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: this.colors.primary,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#e9ecef' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    },

    // Create multi-line chart
    createMultiLineChart: function(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const colors = [
            this.colors.primary,
            this.colors.success,
            this.colors.warning,
            this.colors.danger
        ];

        const datasets = (data.datasets || []).map((dataset, index) => ({
            label: dataset.label,
            data: dataset.values,
            borderColor: colors[index % colors.length],
            backgroundColor: 'transparent',
            borderWidth: 2,
            tension: 0.4,
            pointRadius: 3,
            pointBackgroundColor: colors[index % colors.length]
        }));

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: datasets
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#e9ecef' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    },

    // Create pie chart
    createPieChart: function(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        return new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.labels || [],
                datasets: [{
                    data: data.values || [],
                    backgroundColor: [
                        this.colors.primary,
                        this.colors.success,
                        this.colors.warning,
                        this.colors.danger,
                        this.colors.info
                    ],
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                ...this.defaultOptions
            }
        });
    },

    // Create radar chart (for satisfaction dimensions)
    createRadarChart: function(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        return new Chart(ctx, {
            type: 'radar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: data.label || 'Ratings',
                    data: data.values || [],
                    borderColor: this.colors.primary,
                    backgroundColor: 'rgba(0, 102, 204, 0.1)',
                    pointBackgroundColor: this.colors.primary,
                    borderWidth: 2
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 5,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    },

    // Create horizontal progress bar
    createProgressChart: function(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: data.label || 'Progress',
                    data: data.values || [],
                    backgroundColor: data.colors || this.colors.primary,
                    borderWidth: 0
                }]
            },
            options: {
                ...this.defaultOptions,
                indexAxis: 'y',
                scales: {
                    x: {
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    },
                    y: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.x + '%';
                            }
                        }
                    }
                }
            }
        });
    },

    // Destroy all charts in a container
    destroyChartsInContainer: function(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const canvases = container.querySelectorAll('canvas');
        canvases.forEach(canvas => {
            const chartInstance = Chart.helpers ? Chart.helpers.each([chart], function(instance) {
                instance.destroy();
            }) : null;
            
            // Alternative: look for chart in Chart.instances
            if (window.chartInstances && window.chartInstances[canvas.id]) {
                window.chartInstances[canvas.id].destroy();
                delete window.chartInstances[canvas.id];
            }
        });
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Make ChartConfig available globally
    window.ChartConfig = ChartConfig;
});

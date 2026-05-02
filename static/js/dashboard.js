// Dashboard JavaScript - Real-time queue monitoring with charts

const Dashboard = {
    config: {
        pollInterval: 5000,
        departmentId: '',
        serviceTypeId: '',
        dateRange: 'today'
    },

    charts: {},
    updateTimer: null,

    // Initialize dashboard
    init: function(config) {
        this.config = { ...this.config, ...config };
        console.log('Dashboard initialized', this.config);

        // Set up event listeners
        this.setupEventListeners();

        // Initial data load
        this.refresh();

        // Start polling
        this.startPolling();

        // Handle visibility changes (pause when hidden, resume when visible)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopPolling();
            } else {
                this.startPolling();
            }
        });
    },

    // Set up event listeners
    setupEventListeners: function() {
        const self = this;

        // Filter changes
        document.getElementById('departmentFilter')?.addEventListener('change', (e) => {
            self.config.departmentId = e.target.value;
            self.refresh();
        });

        document.getElementById('serviceTypeFilter')?.addEventListener('change', (e) => {
            self.config.serviceTypeId = e.target.value;
            self.refresh();
        });

        document.getElementById('dateRangeFilter')?.addEventListener('change', (e) => {
            self.config.dateRange = e.target.value;
            self.refresh();
        });
    },

    // Refresh all dashboard data
    refresh: async function() {
        console.log('Dashboard refresh triggered');

        try {
            // Request all data in parallel
            const [kpiData, chartData, queueData] = await Promise.all([
                this.fetchKPIData(),
                this.fetchChartData(),
                this.fetchQueueData()
            ]);

            // Update KPIs
            this.updateKPIs(kpiData);

            // Update charts
            this.updateCharts(chartData);

            // Update queue table
            this.updateQueueTable(queueData);

            // Update timestamp
            this.updateTimestamp();

            notify.success('Dashboard updated', 2000);
        } catch (error) {
            console.error('Dashboard refresh error:', error);
            notify.error('Failed to update dashboard');
        }
    },

    // Fetch KPI data
    fetchKPIData: async function() {
        try {
            return await API.GET('/api/dashboard/kpi/', {
                department: this.config.departmentId,
                service_type: this.config.serviceTypeId,
                date_range: this.config.dateRange
            });
        } catch (error) {
            console.error('KPI fetch error:', error);
            return {};
        }
    },

    // Fetch chart data
    fetchChartData: async function() {
        try {
            return await API.GET('/api/dashboard/charts/', {
                department: this.config.departmentId,
                service_type: this.config.serviceTypeId,
                date_range: this.config.dateRange
            });
        } catch (error) {
            console.error('Chart data fetch error:', error);
            return {};
        }
    },

    // Fetch queue data
    fetchQueueData: async function() {
        try {
            return await API.GET('/api/dashboard/queue/', {
                department: this.config.departmentId,
                service_type: this.config.serviceTypeId,
                date_range: this.config.dateRange
            });
        } catch (error) {
            console.error('Queue data fetch error:', error);
            return { entries: [] };
        }
    },

    // Update KPI cards
    updateKPIs: function(data) {
        // Queue length
        document.getElementById('kpi-queue-length').textContent = data.queue_length || 0;
        
        // Average wait time
        document.getElementById('kpi-avg-wait').textContent = formatTime(data.avg_wait_time || 0);
        
        // Served today
        document.getElementById('kpi-served-today').textContent = data.served_today || 0;
        
        // Throughput
        document.getElementById('kpi-throughput').textContent = (data.throughput || 0).toFixed(1) + '/hr';

        // Update stats
        document.getElementById('stat-total-today').textContent = data.total_today || 0;
        document.getElementById('stat-completed').textContent = data.completed || 0;
        document.getElementById('stat-pending').textContent = data.pending || 0;
        document.getElementById('stat-active-depts').textContent = data.active_depts || 0;
    },

    // Update charts
    updateCharts: function(data) {
        // Destroy existing charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};

        // Queue Status Chart
        if (data.queue_status) {
            document.getElementById('queueStatusLoading').style.display = 'none';
            document.getElementById('queueStatusChart').style.display = 'block';
            
            this.charts.queueStatus = ChartConfig.createQueueStatusChart(
                'queueStatusChart',
                {
                    labels: data.queue_status.labels,
                    values: data.queue_status.values
                }
            );
        }

        // Department Workload Chart
        if (data.dept_workload) {
            document.getElementById('deptWorkloadLoading').style.display = 'none';
            document.getElementById('deptWorkloadChart').style.display = 'block';
            
            this.charts.deptWorkload = ChartConfig.createDepartmentBarChart(
                'deptWorkloadChart',
                {
                    labels: data.dept_workload.labels,
                    values: data.dept_workload.values
                }
            );
        }

        // Service Distribution Chart
        if (data.service_dist) {
            document.getElementById('serviceDistLoading').style.display = 'none';
            document.getElementById('serviceDistChart').style.display = 'block';
            
            this.charts.serviceDist = ChartConfig.createPieChart(
                'serviceDistChart',
                {
                    labels: data.service_dist.labels,
                    values: data.service_dist.values
                }
            );
        }

        // Wait Time Trend Chart
        if (data.wait_trend) {
            document.getElementById('waitTrendLoading').style.display = 'none';
            document.getElementById('waitTrendChart').style.display = 'block';
            
            this.charts.waitTrend = ChartConfig.createTrendLineChart(
                'waitTrendChart',
                {
                    label: 'Average Wait Time (minutes)',
                    labels: data.wait_trend.labels,
                    values: data.wait_trend.values
                }
            );
        }
    },

    // Update queue table
    updateQueueTable: function(data) {
        const tbody = document.getElementById('queueTableBody');
        const loading = document.getElementById('queueTableLoading');
        const table = document.getElementById('queueTable');

        loading.style.display = 'none';
        table.style.display = 'table';

        tbody.innerHTML = '';

        if (!data.entries || data.entries.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No active tickets</td></tr>';
            return;
        }

        data.entries.forEach(entry => {
            const statusColor = getStatusColor(entry.status);
            const statusIcon = getStatusIcon(entry.status);
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${entry.ticket_number || entry.queue_number}</strong></td>
                <td>${entry.customer_name || entry.name || '-'}</td>
                <td>${entry.service_type}</td>
                <td>
                    <span class="badge" style="background-color: ${statusColor}">
                        <i class="fas ${statusIcon}"></i> ${entry.status}
                    </span>
                </td>
                <td>${formatTime(entry.wait_time_minutes || 0)}</td>
                <td>${entry.department}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="Dashboard.updateTicketStatus(${entry.id}, 'IN_PROGRESS')">
                        <i class="fas fa-play"></i> Start
                    </button>
                    <button class="btn btn-sm btn-outline-success" onclick="Dashboard.updateTicketStatus(${entry.id}, 'COMPLETED')">
                        <i class="fas fa-check"></i> Done
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    },

    // Update ticket status
    updateTicketStatus: async function(entryId, status) {
        try {
            const response = await API.POST(`/queues/update/${entryId}/`, {
                status: status
            });

            notify.success(`Ticket updated to ${status}`);
            this.refresh();
        } catch (error) {
            console.error('Status update error:', error);
            notify.error('Failed to update ticket status');
        }
    },

    // Update timestamp
    updateTimestamp: function() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });

        document.getElementById('lastUpdate').textContent = timeStr;
        document.getElementById('stat-last-update').textContent = timeStr;
    },

    // Start polling
    startPolling: function() {
        if (this.updateTimer) return; // Already polling

        console.log('Dashboard polling started');
        
        this.updateTimer = setInterval(() => {
            this.refresh();
        }, this.config.pollInterval);
    },

    // Stop polling
    stopPolling: function() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
            console.log('Dashboard polling stopped');
        }
    }
};

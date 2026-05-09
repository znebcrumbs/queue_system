// Admin Analytics Dashboard

const AdminAnalytics = {
    filters: {
        startDate: null,
        endDate: null,
        department: '',
        serviceType: ''
    },

    charts: {},

    // Initialize analytics
    init: function() {
        console.log('Admin Analytics initialized');

        // Set default date range (last 30 days)
        const today = new Date();
        const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));

        document.getElementById('filterStartDate').value = thirtyDaysAgo.toISOString().split('T')[0];
        document.getElementById('filterEndDate').value = today.toISOString().split('T')[0];

        // Set up event listeners
        this.setupEventListeners();

        // Initial data load
        this.loadData();
    },

    // Set up event listeners
    setupEventListeners: function() {
        document.getElementById('filterStartDate').addEventListener('change', () => {
            this.applyFilters();
        });

        document.getElementById('filterEndDate').addEventListener('change', () => {
            this.applyFilters();
        });

        document.getElementById('filterDepartment').addEventListener('change', () => {
            this.applyFilters();
        });

        document.getElementById('filterServiceType').addEventListener('change', () => {
            this.applyFilters();
        });
    },

    // Apply filters
    applyFilters: function() {
        this.filters.startDate = document.getElementById('filterStartDate').value;
        this.filters.endDate = document.getElementById('filterEndDate').value;
        this.filters.department = document.getElementById('filterDepartment').value;
        this.filters.serviceType = document.getElementById('filterServiceType').value;

        console.log('Filters applied:', this.filters);
        this.loadData();
    },

    // Load all data
    loadData: async function() {
        try {
            const [kpiData, chartData, tableData, auditData] = await Promise.all([
                this.fetchKPIData(),
                this.fetchChartData(),
                this.fetchTableData(),
                this.fetchAuditData()
            ]);

            this.updateKPIs(kpiData);
            this.updateCharts(chartData);
            this.updateTables(tableData);
            this.updateAudit(auditData);

            notify.success('Analytics updated successfully', 2000);
        } catch (error) {
            console.error('Analytics load error:', error);
            notify.error('Failed to load analytics');
        }
    },

    // Fetch KPI data
    fetchKPIData: async function() {
        try {
            return await API.GET('/api/admin/analytics/kpi/', this.filters);
        } catch (error) {
            console.error('KPI fetch error:', error);
            return {};
        }
    },

    // Fetch chart data
    fetchChartData: async function() {
        try {
            return await API.GET('/api/admin/analytics/charts/', this.filters);
        } catch (error) {
            console.error('Chart data fetch error:', error);
            return {};
        }
    },

    // Fetch table data
    fetchTableData: async function() {
        try {
            return await API.GET('/api/admin/analytics/tables/', this.filters);
        } catch (error) {
            console.error('Table data fetch error:', error);
            return {};
        }
    },

    // Fetch audit data
    fetchAuditData: async function() {
        try {
            return await API.GET('/api/admin/analytics/audit/', { ...this.filters, limit: 20 });
        } catch (error) {
            console.error('Audit data fetch error:', error);
            return { entries: [] };
        }
    },

    // Update KPI cards
    updateKPIs: function(data) {
        document.getElementById('kpi-total-tickets').textContent = data.total_tickets || 0;
        document.getElementById('kpi-completion-rate').textContent = (data.completion_rate || 0).toFixed(1) + '%';
        document.getElementById('kpi-avg-resolution').textContent = formatTime(data.avg_resolution_time || 0);
        document.getElementById('kpi-satisfaction').textContent = (data.satisfaction_score || 0).toFixed(1) + '★';
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

        // Ticket Volume Trend
        if (data.ticket_volume) {
            this.charts.ticketVolume = ChartConfig.createTrendLineChart(
                'ticketVolumeTrendChart',
                {
                    label: 'Tickets',
                    labels: data.ticket_volume.labels,
                    values: data.ticket_volume.values
                }
            );
        }

        // Department Performance
        if (data.dept_performance) {
            this.charts.deptPerformance = ChartConfig.createDepartmentBarChart(
                'deptPerformanceChart',
                {
                    labels: data.dept_performance.labels,
                    values: data.dept_performance.values
                }
            );
        }

        // Service Type Distribution
        if (data.service_dist) {
            this.charts.serviceDist = ChartConfig.createPieChart(
                'serviceTypeDistChart',
                {
                    labels: data.service_dist.labels,
                    values: data.service_dist.values
                }
            );
        }

        // Average Resolution Time
        if (data.resolution_time) {
            this.charts.resolutionTime = ChartConfig.createTrendLineChart(
                'resolutionTimeChart',
                {
                    label: 'Resolution Time (minutes)',
                    labels: data.resolution_time.labels,
                    values: data.resolution_time.values
                }
            );
        }

        // Staff Productivity
        if (data.staff_productivity) {
            this.charts.staffProductivity = ChartConfig.createDepartmentBarChart(
                'staffProductivityChart',
                {
                    labels: data.staff_productivity.labels,
                    values: data.staff_productivity.values
                }
            );
        }

        // Customer Satisfaction Trend
        if (data.satisfaction_trend) {
            this.charts.satisfactionTrend = ChartConfig.createTrendLineChart(
                'satisfactionTrendChart',
                {
                    label: 'Satisfaction Score',
                    labels: data.satisfaction_trend.labels,
                    values: data.satisfaction_trend.values
                }
            );
        }
    },

    // Update tables
    updateTables: function(data) {
        // Department Performance Table
        if (data.departments) {
            const deptTable = document.querySelector('#deptTable tbody');
            deptTable.innerHTML = '';

            data.departments.forEach(dept => {
                const row = deptTable.insertRow();
                row.innerHTML = `
                    <td><strong>${dept.name}</strong></td>
                    <td>${dept.total}</td>
                    <td>${dept.completed}</td>
                    <td>${dept.pending}</td>
                    <td>
                        <span class="badge badge-success">${(dept.completion_rate || 0).toFixed(1)}%</span>
                    </td>
                    <td>${formatTime(dept.avg_wait_time || 0)}</td>
                    <td>${formatTime(dept.avg_resolution_time || 0)}</td>
                `;
            });
        }

        // Service Type Performance Table
        if (data.services) {
            const serviceTable = document.querySelector('#serviceTable tbody');
            serviceTable.innerHTML = '';

            data.services.forEach(service => {
                const row = serviceTable.insertRow();
                row.innerHTML = `
                    <td><strong>${service.name}</strong></td>
                    <td>${service.total}</td>
                    <td>${service.completed}</td>
                    <td>
                        <span class="badge badge-success">${(service.success_rate || 0).toFixed(1)}%</span>
                    </td>
                    <td>${formatTime(service.avg_wait_time || 0)}</td>
                    <td>${formatTime(service.avg_resolution_time || 0)}</td>
                `;
            });
        }

        // Staff Performance Table
        if (data.staff) {
            const staffTable = document.querySelector('#staffTable tbody');
            staffTable.innerHTML = '';

            data.staff.forEach(staff => {
                const row = staffTable.insertRow();
                row.innerHTML = `
                    <td><strong>${staff.name}</strong></td>
                    <td>${staff.department}</td>
                    <td>${staff.tickets_processed}</td>
                    <td>${formatTime(staff.avg_resolution_time || 0)}</td>
                    <td>
                        <i class="fas fa-star"></i> ${(staff.rating || 0).toFixed(1)}
                    </td>
                `;
            });
        }
    },

    // Update audit table
    updateAudit: function(data) {
        const auditTable = document.querySelector('#auditTable tbody');
        auditTable.innerHTML = '';

        if (!data.entries || data.entries.length === 0) {
            auditTable.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No recent activity</td></tr>';
            return;
        }

        data.entries.forEach(entry => {
            const row = auditTable.insertRow();
            const timestamp = new Date(entry.timestamp).toLocaleString();
            row.innerHTML = `
                <td>${timestamp}</td>
                <td><span class="badge badge-primary">${entry.action}</span></td>
                <td>${entry.user || '-'}</td>
                <td>${entry.object_name || entry.object_type}</td>
                <td>${entry.description || '-'}</td>
            `;
        });
    },

    // Export PDF
    exportPDF: function() {
        const element = document.querySelector('.admin-analytics-container');
        const opt = {
            margin: 10,
            filename: 'queue-system-analytics-' + new Date().toISOString().split('T')[0] + '.pdf',
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { orientation: 'portrait', unit: 'mm', format: 'a4' }
        };

        html2pdf().set(opt).from(element).save();
    }
};

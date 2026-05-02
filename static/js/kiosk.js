// Kiosk Form JavaScript - Multi-step form handler

const Kiosk = {
    config: {
        departmentsData: [],
        serviceTypesData: []
    },

    currentStep: 1,
    formData: {},

    // Initialize kiosk
    init: function(config) {
        this.config = { ...this.config, ...config };
        console.log('Kiosk initialized with config:', this.config);
        console.log('Service types data:', this.config.serviceTypesData);

        // Set up event listeners
        this.setupEventListeners();

        // Populate service types when department changes
        this.loadServiceTypes();
    },

    // Set up event listeners
    setupEventListeners: function() {
        const form = document.getElementById('kioskForm');
        const deptSelect = document.getElementById('department');

        // Form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitForm();
        });

        // Department change
        deptSelect.addEventListener('change', () => {
            this.loadServiceTypes();
        });

        // Real-time validation
        document.getElementById('customerName').addEventListener('blur', () => {
            this.validateName();
        });

        document.getElementById('customerPhone').addEventListener('blur', () => {
            this.validatePhone();
        });

        document.getElementById('customerEmail').addEventListener('blur', () => {
            this.validateEmail();
        });
    },

    // Load service types based on selected department
    loadServiceTypes: function() {
        const deptId = document.getElementById('department').value;
        const deptSelect = document.getElementById('department');
        
        if (!deptId) {
            document.getElementById('serviceTypeGroup').style.display = 'none';
            return;
        }

        // Get department name and selected value
        const deptName = deptSelect.options[deptSelect.selectedIndex]?.text;
        this.formData.department = deptId;
        this.formData.departmentName = deptName;

        // Try to use config data first, fallback to API
        let serviceTypes = [];
        
        if (this.config.serviceTypesData && this.config.serviceTypesData.length > 0) {
            console.log('Using config serviceTypesData');
            serviceTypes = this.config.serviceTypesData.filter(s => s.department_id == deptId);
        } else {
            console.log('Config data empty, using API fallback');
            // Use API fallback
            this.loadServiceTypesFromAPI(deptId);
            return;
        }

        this.renderServiceButtons(serviceTypes);
    },

    // Load service types from API (fallback)
    loadServiceTypesFromAPI: function(deptId) {
        fetch(`/queues/api/services/?department_id=${deptId}`)
            .then(response => response.json())
            .then(services => {
                console.log('Loaded services from API:', services);
                this.renderServiceButtons(services);
            })
            .catch(error => {
                console.error('Error loading services:', error);
                const grid = document.getElementById('serviceTypeGrid');
                grid.innerHTML = '<p class="text-danger">Error loading services. Check console.</p>';
            });
    },

    // Render service type buttons
    renderServiceButtons: function(serviceTypes) {
        const grid = document.getElementById('serviceTypeGrid');
        grid.innerHTML = '';

        if (!serviceTypes || serviceTypes.length === 0) {
            grid.innerHTML = '<p class="text-muted">No services available</p>';
            document.getElementById('serviceTypeGroup').style.display = 'none';
            console.log('No service types to display');
            return;
        }

        serviceTypes.forEach(service => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'service-type-button';
            button.onclick = (e) => {
                e.preventDefault();
                this.selectServiceType(service);
            };
            button.innerHTML = `
                <i class="fas fa-${this.getServiceIcon(service.name)}"></i>
                <span>${service.name}</span>
            `;

            if (this.formData.serviceType === service.id) {
                button.classList.add('selected');
            }

            grid.appendChild(button);
        });

        document.getElementById('serviceTypeGroup').style.display = 'block';
        console.log(`Rendered ${serviceTypes.length} service buttons`);
    },

    // Select service type
    selectServiceType: function(service) {
        const buttons = document.querySelectorAll('.service-type-button');
        buttons.forEach(btn => btn.classList.remove('selected'));
        
        event.target.closest('.service-type-button').classList.add('selected');
        
        this.formData.serviceType = service.id;
        this.formData.serviceTypeName = service.name;
    },

    // Get icon for service type
    getServiceIcon: function(serviceName) {
        const icons = {
            'registration': 'fa-edit',
            'inquiry': 'fa-question-circle',
            'complaint': 'fa-exclamation-triangle',
            'feedback': 'fa-star',
            'payment': 'fa-credit-card'
        };

        for (const [key, icon] of Object.entries(icons)) {
            if (serviceName.toLowerCase().includes(key)) {
                return icon;
            }
        }
        return 'fa-list';
    },

    // Move to next step
    nextStep: function(currentStep) {
        // Validate current step
        if (!this.validateStep(currentStep)) {
            notify.warning('Please fill in all required fields');
            return;
        }

        // Hide current step
        document.querySelector(`.kiosk-step[data-step="${currentStep}"]`).classList.remove('active');
        document.querySelector(`.progress-step[data-step="${currentStep}"]`).classList.add('completed');

        // Show next step
        this.currentStep = currentStep + 1;
        document.querySelector(`.kiosk-step[data-step="${this.currentStep}"]`).classList.add('active');
        document.querySelector(`.progress-step[data-step="${this.currentStep}"]`).classList.add('active');

        // Update confirmation on step 3
        if (this.currentStep === 3) {
            this.updateConfirmation();
        }

        // Scroll to top
        document.querySelector('.kiosk-wrapper').scrollTop = 0;
    },

    // Move to previous step
    prevStep: function(currentStep) {
        // Hide current step
        document.querySelector(`.kiosk-step[data-step="${currentStep}"]`).classList.remove('active');
        document.querySelector(`.progress-step[data-step="${currentStep}"]`).classList.remove('active');

        // Show previous step
        this.currentStep = currentStep - 1;
        document.querySelector(`.kiosk-step[data-step="${this.currentStep}"]`).classList.add('active');
        document.querySelector(`.progress-step[data-step="${this.currentStep}"]`).classList.remove('completed');

        // Scroll to top
        document.querySelector('.kiosk-wrapper').scrollTop = 0;
    },

    // Validate step
    validateStep: function(step) {
        switch (step) {
            case 1:
                // Check if department and service type are selected
                if (!this.formData.department || !this.formData.serviceType) {
                    return false;
                }
                break;
            case 2:
                // Check if name is filled
                if (!document.getElementById('customerName').value.trim()) {
                    return false;
                }
                break;
        }
        return true;
    },

    // Validate name
    validateName: function() {
        const name = document.getElementById('customerName').value.trim();
        const error = document.getElementById('nameError');

        if (!name) {
            error.textContent = 'Name is required';
            error.style.display = 'block';
            return false;
        }

        if (name.length < 2) {
            error.textContent = 'Name must be at least 2 characters';
            error.style.display = 'block';
            return false;
        }

        error.style.display = 'none';
        return true;
    },

    // Validate phone
    validatePhone: function() {
        const phone = document.getElementById('customerPhone').value;
        if (phone && !/^[0-9\s\-\+\(\)]{7,}$/.test(phone)) {
            notify.warning('Please enter a valid phone number');
            return false;
        }
        return true;
    },

    // Validate email
    validateEmail: function() {
        const email = document.getElementById('customerEmail').value;
        if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            notify.warning('Please enter a valid email address');
            return false;
        }
        return true;
    },

    // Update confirmation display
    updateConfirmation: function() {
        document.getElementById('confirmDept').textContent = this.formData.departmentName || '-';
        document.getElementById('confirmService').textContent = this.formData.serviceTypeName || '-';
        document.getElementById('confirmName').textContent = document.getElementById('customerName').value || '-';
        document.getElementById('confirmPhone').textContent = document.getElementById('customerPhone').value || '-';
    },

    // Submit form
    submitForm: async function() {
        // Collect form data
        const formData = {
            department_id: this.formData.department,
            service_type_id: this.formData.serviceType,
            customer_name: document.getElementById('customerName').value,
            customer_phone: document.getElementById('customerPhone').value,
            customer_email: document.getElementById('customerEmail').value,
            customer_id: document.getElementById('customerId').value
        };

        try {
            // Submit to server - public kiosk endpoint without API key requirement
            const response = await API.POST('/queues/create-public/', formData);

            // Show success modal
            this.showSuccessModal(response);

            notify.success('Ticket created successfully!');
        } catch (error) {
            console.error('Form submission error:', error);
            notify.error('Failed to create ticket: ' + (error.message || 'Unknown error'));
        }
    },

    // Show success modal
    showSuccessModal: function(response) {
        // Update ticket number and QR
        document.getElementById('successTicketNumber').textContent = response.ticket_number || response.queue_number;

        if (response.qr_code_url) {
            document.getElementById('successQRCode').src = response.qr_code_url;
        }

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('successModal'));
        modal.show();
    },

    // Reset form for next ticket
    reset: function() {
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('successModal'));
        modal.hide();

        // Reset form
        document.getElementById('kioskForm').reset();
        this.formData = {};
        this.currentStep = 1;

        // Reset progress
        document.querySelectorAll('.progress-step').forEach((step, index) => {
            step.classList.remove('completed', 'active');
            if (index === 0) step.classList.add('active');
        });

        // Reset steps display
        document.querySelectorAll('.kiosk-step').forEach(step => {
            step.classList.remove('active');
        });
        document.querySelector('.kiosk-step[data-step="1"]').classList.add('active');

        // Hide service types
        document.getElementById('serviceTypeGroup').style.display = 'none';

        // Scroll to top
        window.scrollTo(0, 0);
    }
};

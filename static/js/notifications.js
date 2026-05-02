// Toast Notification System

const Notifications = {
    container: null,

    init: function() {
        this.container = document.getElementById('toastContainer');
    },

    show: function(message, type = 'info', duration = 5000) {
        if (!this.container) this.init();

        // Create toast element
        const toastId = 'toast-' + Date.now();
        const toastHTML = `
            <div id="${toastId}" class="toast fade show" role="alert" aria-live="assertive">
                <div class="toast-header bg-${type === 'error' ? 'danger' : type} text-white">
                    <i class="fas fa-${this._getIcon(type)} me-2"></i>
                    <strong class="me-auto">${this._getTitle(type)}</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        // Add to container
        this.container.insertAdjacentHTML('beforeend', toastHTML);
        const toastElement = document.getElementById(toastId);

        // Initialize Bootstrap Toast
        const toast = new bootstrap.Toast(toastElement);
        toast.show();

        // Remove element after hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });

        // Auto hide after duration
        if (duration > 0) {
            setTimeout(() => {
                if (toastElement.classList.contains('show')) {
                    toast.hide();
                }
            }, duration);
        }
    },

    success: function(message, duration = 5000) {
        this.show(message, 'success', duration);
    },

    error: function(message, duration = 0) {
        this.show(message, 'error', duration);
    },

    warning: function(message, duration = 5000) {
        this.show(message, 'warning', duration);
    },

    info: function(message, duration = 5000) {
        this.show(message, 'info', duration);
    },

    _getIcon: function(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'circle';
    },

    _getTitle: function(type) {
        const titles = {
            'success': 'Success',
            'error': 'Error',
            'warning': 'Warning',
            'info': 'Info'
        };
        return titles[type] || 'Notification';
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    Notifications.init();
});

// Export for use in other scripts
window.notify = Notifications;

// Utility Functions

/**
 * API Client for AJAX requests
 */
const API = {
    GET: async function(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        
        try {
            const response = await fetch(fullUrl, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin'
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API GET Error:', error);
            throw error;
        }
    },

    POST: async function(url, data = {}) {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API POST Error:', error);
            throw error;
        }
    },

    DELETE: async function(url) {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        
        try {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin'
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API DELETE Error:', error);
            throw error;
        }
    }
};

/**
 * Debounce function
 */
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

/**
 * Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Format number as currency
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

/**
 * Format number with thousand separator
 */
function formatNumber(value) {
    return new Intl.NumberFormat('en-US').format(value);
}

/**
 * Format time as HH:MM
 */
function formatTime(minutes) {
    if (!minutes) return '0 min';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    
    if (hours === 0) return `${mins} min`;
    if (mins === 0) return `${hours} hr`;
    return `${hours}h ${mins}m`;
}

/**
 * Format date
 */
function formatDate(date, format = 'short') {
    const d = new Date(date);
    if (format === 'short') {
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }
    return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
}

/**
 * Get CSRF token from DOM
 */
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

/**
 * Add CSRF token to forms
 */
function addCsrfToForms() {
    const csrftoken = getCsrfToken();
    document.querySelectorAll('form').forEach(form => {
        if (!form.querySelector('[name=csrfmiddlewaretoken]')) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'csrfmiddlewaretoken';
            input.value = csrftoken;
            form.appendChild(input);
        }
    });
}

/**
 * Check if element is in viewport
 */
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Get color by status
 */
function getStatusColor(status) {
    const colors = {
        'PENDING': '#ffc107',
        'WAITING': '#17a2b8',
        'IN_PROGRESS': '#007bff',
        'COMPLETED': '#28a745',
        'SERVED': '#28a745',
        'CANCELLED': '#dc3545',
        'RETURNED': '#fd7e14',
    };
    return colors[status] || '#6c757d';
}

/**
 * Get icon by status
 */
function getStatusIcon(status) {
    const icons = {
        'PENDING': 'fa-hourglass',
        'WAITING': 'fa-clock',
        'IN_PROGRESS': 'fa-spinner',
        'COMPLETED': 'fa-check-circle',
        'SERVED': 'fa-check-circle',
        'CANCELLED': 'fa-times-circle',
        'RETURNED': 'fa-redo',
    };
    return icons[status] || 'fa-circle';
}

/**
 * Sanitize HTML
 */
function sanitizeHtml(html) {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
}

// Initialize CSRF on page load
document.addEventListener('DOMContentLoaded', addCsrfToForms);

/**
 * Get the relative URL for a monitor
 * @param {number} id - The monitor ID
 * @returns {string} The relative URL
 */
export function getMonitorRelativeURL(id) {
    return `/monitor/${id}`;
}

/**
 * Format a date to a relative time string
 * @param {Date|string} date - The date to format
 * @returns {string} The formatted date
 */
export function formatRelativeTime(date) {
    if (!date) return '';
    
    const now = new Date();
    const then = new Date(date);
    const diff = now - then;
    
    // Less than 1 minute
    if (diff < 60000) {
        return 'just now';
    }
    
    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}m ago`;
    }
    
    // Less than 1 day
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}h ago`;
    }
    
    // Less than 1 week
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days}d ago`;
    }
    
    // Less than 1 month
    if (diff < 2592000000) {
        const weeks = Math.floor(diff / 604800000);
        return `${weeks}w ago`;
    }
    
    // Less than 1 year
    if (diff < 31536000000) {
        const months = Math.floor(diff / 2592000000);
        return `${months}mo ago`;
    }
    
    const years = Math.floor(diff / 31536000000);
    return `${years}y ago`;
}

/**
 * Format a date to a localized string
 * @param {Date|string} date - The date to format
 * @returns {string} The formatted date
 */
export function formatDate(date) {
    if (!date) return '';
    return new Date(date).toLocaleString();
}

/**
 * Format a duration in milliseconds to a human readable string
 * @param {number} ms - The duration in milliseconds
 * @returns {string} The formatted duration
 */
export function formatDuration(ms) {
    if (!ms) return '0ms';
    
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes % 60}m`;
    }
    if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
} 
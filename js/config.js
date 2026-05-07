/**
 * Douéra Shop - Global Configuration
 */
// Si on est en local mais pas sur le port 5001 (ex: Live Server), on pointe vers 5001
const API_BASE_URL = (window.location.protocol === 'file:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? (window.location.port === '5001' ? '/api' : 'http://localhost:5001/api')
    : '/api';

// Export pour usage global
window.API_CONFIG = {
    BASE_URL: API_BASE_URL
};

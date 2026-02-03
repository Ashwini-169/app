/**
 * API configuration with normalized base URL
 * Ensures no double slashes in API calls
 */

// Get API base from environment or fallback to localhost
const API_BASE = (process.env.REACT_APP_API_URL || 'http://localhost:8002').replace(/\/$/, '');

export default API_BASE;

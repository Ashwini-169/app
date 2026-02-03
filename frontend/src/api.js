/**
 * API configuration with normalized base URL
 * Ensures no double slashes in API calls
 * REQUIRES REACT_APP_API_URL to be defined at build time
 */

const API_BASE = process.env.REACT_APP_API_URL;

if (!API_BASE) {
  throw new Error(
    'REACT_APP_API_URL is not defined at build time. ' +
    'Pass it as a build ARG in Dockerfile: ARG REACT_APP_API_URL'
  );
}

export default API_BASE.replace(/\/$/, '');

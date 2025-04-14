/**
 * Utility functions for API interactions
 */

// The base URL for the backend API, with fallback to default
const getBaseUrl = () => {
  // Try to get from environment variables first (Vite uses import.meta.env)
  if (typeof import.meta !== 'undefined' && import.meta.env) {
    if (import.meta.env.VITE_API_URL) {
      return import.meta.env.VITE_API_URL.replace(/\/$/, ''); // Remove trailing slash if present
    }
  }
  
  // Fallback to default
  return 'http://localhost:8000';
};

// Initialize API_BASE_URL
const API_BASE_URL = getBaseUrl();
console.log(`API base URL: ${API_BASE_URL}`);

/**
 * Constructs a full API URL from a path
 * @param {string} path - API endpoint path (should start with '/')
 * @returns {string} Complete API URL
 */
export const getApiUrl = (path) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
};

/**
 * Parse API error responses
 * @param {Response} response - Fetch API response object
 * @returns {Promise<string>} Error message
 */
export const parseApiError = async (response) => {
  try {
    // Check if there's content to parse
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const errorData = await response.json();
      // Handle various error formats the API might return
      if (errorData.detail) {
        return Array.isArray(errorData.detail) 
          ? errorData.detail.map(err => err.msg).join(', ')
          : errorData.detail;
      } else if (errorData.message) {
        return errorData.message;
      } else {
        return `API Error: ${response.status} ${response.statusText}`;
      }
    } else {
      // If not JSON content
      const text = await response.text();
      return text || `API Error: ${response.status} ${response.statusText}`;
    }
  } catch (error) {
    console.error('Error parsing API error:', error);
    return `API Error: ${response.status} ${response.statusText}`;
  }
};

/**
 * Handles common API error scenarios
 * @param {Error} error - The caught error
 * @returns {string} User-friendly error message
 */
export const handleApiError = (error) => {
  if (error.name === 'AbortError') {
    return 'Request timed out. Please check your connection and try again.';
  }
  
  if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
    return 'Network error. Please check your connection and try again.';
  }
  
  return error.message || 'An unexpected error occurred. Please try again.';
};

/**
 * Makes a fetch request with retry capabilities
 * @param {string} url - The URL to fetch
 * @param {Object} options - Fetch options
 * @param {Object} retryOptions - Options for retries
 * @returns {Promise<Response>} Fetch response
 */
export const fetchWithRetry = async (
  url, 
  options = {}, 
  { maxRetries = 3, retryDelay = 1000, timeout = 10000 } = {}
) => {
  let lastError;
  
  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  // Add signal to options
  options.signal = controller.signal;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      lastError = error;
      
      // Don't retry if it was a timeout or user abort
      if (error.name === 'AbortError') {
        clearTimeout(timeoutId);
        throw error;
      }
      
      // Don't retry on the last attempt
      if (attempt === maxRetries - 1) {
        clearTimeout(timeoutId);
        throw error;
      }
      
      console.warn(`API request failed (attempt ${attempt + 1}/${maxRetries}), retrying...`, error);
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, retryDelay));
      
      // Increase delay for next retry (exponential backoff)
      retryDelay *= 2;
    }
  }
  
  // If we get here, all retries failed
  clearTimeout(timeoutId);
  throw lastError;
};

/**
 * Check if the backend server is running
 * @returns {Promise<boolean>} True if server is reachable
 */
export const checkBackendStatus = async () => {
  try {
    const response = await fetchWithRetry(
      getApiUrl('/api'), 
      { method: 'GET' },
      { maxRetries: 1, timeout: 3000 }
    );
    return response.ok;
  } catch (error) {
    console.error('Backend status check failed:', error);
    return false;
  }
}; 
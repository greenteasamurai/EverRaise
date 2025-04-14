// Authentication utility functions
import { getApiUrl } from './api';

const TOKEN_KEY = 'everraise_token';
const TOKEN_EXPIRY_KEY = 'everraise_token_expiry';
const TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000; // 5 minutes in milliseconds

/**
 * Store authentication token in localStorage with expiry time
 * @param {string} token - JWT token to store
 */
export const setToken = (token) => {
  if (!token) {
    console.error('Attempted to store empty token');
    return;
  }
  
  // Store the token
  localStorage.setItem(TOKEN_KEY, token);
  
  // Parse and store expiry time if it's a JWT token
  try {
    const payload = parseJwt(token);
    if (payload && payload.exp) {
      // Convert exp (in seconds) to milliseconds
      const expiryTime = payload.exp * 1000;
      localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
      console.log(`Token will expire at: ${new Date(expiryTime).toLocaleString()}`);
    }
  } catch (error) {
    console.error('Failed to parse token expiry:', error);
  }
  
  console.log('Token stored successfully');
};

/**
 * Parse JWT token to get payload
 * @param {string} token - JWT token to parse
 * @returns {object|null} Parsed token payload or null if invalid
 */
export const parseJwt = (token) => {
  try {
    // For JWT format: header.payload.signature
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error parsing JWT token:', error);
    return null;
  }
};

/**
 * Get the authentication token from localStorage
 * @returns {string|null} The stored token or null if not found
 */
export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Get the token expiry timestamp
 * @returns {number|null} Token expiry timestamp in milliseconds or null
 */
export const getTokenExpiry = () => {
  const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
  return expiry ? parseInt(expiry, 10) : null;
};

/**
 * Remove token from localStorage (logout)
 */
export const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TOKEN_EXPIRY_KEY);
};

/**
 * Check if the token is expired or about to expire
 * @returns {boolean} True if token is expired or will expire soon
 */
export const isTokenExpired = () => {
  const expiry = getTokenExpiry();
  if (!expiry) return false;
  
  // Check if token is expired or will expire within the threshold
  const now = Date.now();
  return now > (expiry - TOKEN_REFRESH_THRESHOLD);
};

/**
 * Check if the user is authenticated with a valid token
 * @returns {boolean} True if authenticated with valid token
 */
export const isAuthenticated = () => {
  const token = getToken();
  if (!token) return false;
  
  // Only return true if token is not expired
  const expiry = getTokenExpiry();
  if (expiry) {
    const now = Date.now();
    return now < expiry;
  }
  
  return !!token; // Fallback if expiry not set
};

/**
 * Attempt to refresh the authentication token if it's expiring soon
 * @returns {Promise<boolean>} True if token was refreshed successfully
 */
export const refreshTokenIfNeeded = async () => {
  if (!getToken() || !isTokenExpired()) {
    return false; // No token or not expired, no need to refresh
  }
  
  console.log('Token expiring soon, attempting refresh...');
  
  try {
    const response = await fetch(getApiUrl('/api/v1/auth/refresh-token'), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.access_token) {
        setToken(data.access_token);
        console.log('Token refreshed successfully');
        return true;
      }
    }
    
    console.warn('Failed to refresh token, status:', response.status);
    return false;
  } catch (error) {
    console.error('Error refreshing token:', error);
    return false;
  }
};

/**
 * Helper function to make authenticated API requests with token refresh
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @param {number} timeout - Optional timeout in milliseconds
 * @returns {Promise} Fetch promise
 */
export const authenticatedFetch = async (url, options = {}, timeout = 30000) => {
  // Try to refresh token if needed before making the request
  await refreshTokenIfNeeded();
  
  const token = getToken();
  
  if (!token) {
    throw new Error('No authentication token found. Please log in first.');
  }
  
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
    ...(options.headers || {})
  };
  
  // Create abort controller for timeout
  const controller = new AbortController();
  const { signal } = controller;
  
  // Set timeout to abort request if it takes too long
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal
    });
    
    // Clear timeout since request completed
    clearTimeout(timeoutId);
    
    if (response.status === 401) {
      console.error('Authentication failed. Token may be expired.');
      
      // Try token refresh on 401 (one-time attempt)
      const refreshed = await refreshTokenIfNeeded();
      if (refreshed) {
        // Retry the request with the new token
        console.log('Retrying request with refreshed token');
        return authenticatedFetch(url, options, timeout);
      }
      
      // If refresh failed, clear token and notify
      removeToken(); // Clear the invalid token
      throw new Error('Authentication failed. Please log in again.');
    }
    
    if (!response.ok) {
      // Try to parse error response if it's JSON
      try {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API error: ${response.status}`);
      } catch (e) {
        // If not JSON or other error
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
    }
    
    // Check if response is empty
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }
    
    return response.text();
  } catch (error) {
    // Clear timeout to prevent memory leaks
    clearTimeout(timeoutId);
    
    // Add specific error message for timeouts
    if (error.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeout}ms`);
    }
    
    throw error;
  }
}; 
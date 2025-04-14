// Authentication utility functions
const TOKEN_KEY = 'everraise_token';

/**
 * Store authentication token in localStorage
 * @param {string} token - JWT token to store
 */
export const setToken = (token: string): void => {
  if (!token) {
    console.error('Attempted to store empty token');
    return;
  }
  localStorage.setItem(TOKEN_KEY, token);
  console.log('Token stored successfully');
};

/**
 * Get the authentication token from localStorage
 * @returns {string|null} The stored token or null if not found
 */
export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Remove the authentication token from localStorage
 */
export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
  console.log('Token removed successfully');
};

/**
 * Check if the user is authenticated (has a token)
 * @returns {boolean} True if authenticated
 */
export const isAuthenticated = (): boolean => {
  const token = getToken();
  return !!token;
};

/**
 * Helper function to make authenticated API requests
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @param {number} timeout - Optional timeout in milliseconds
 * @returns {Promise} Fetch promise
 */
export const authenticatedFetch = async (url: string, options: RequestInit = {}, timeout: number = 30000): Promise<any> => {
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
      // Here you could redirect to login or handle token refresh
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
  } catch (error: any) {
    // Clear timeout to prevent memory leaks
    clearTimeout(timeoutId);
    
    // Add specific error message for timeouts
    if (error.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeout}ms`);
    }
    
    throw error;
  }
}; 
/**
 * API utilities for managing API URLs and endpoints
 */

/**
 * Get the base API URL from environment variables
 * This allows the API URL to be configured at build/runtime
 */
export const getApiBaseUrl = (): string => {
  // Get from environment variable or use default
  // In Vite, environment variables must be explicitly declared with the VITE_ prefix
  // @ts-ignore -- Vite-specific environment variables
  return import.meta.env.VITE_API_URL || 'http://localhost:8000';
};

/**
 * Build a complete API URL for a specific endpoint
 * 
 * @param endpoint - The API endpoint (should start with '/')
 * @returns The complete API URL
 */
export const getApiUrl = (endpoint: string): string => {
  const baseUrl = getApiBaseUrl();
  const formattedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${formattedEndpoint}`;
};

/**
 * Create a fetch request with timeout
 * 
 * @param url - The URL to fetch
 * @param options - Fetch options
 * @param timeout - Timeout in milliseconds
 * @returns Promise with the fetch response
 */
export const fetchWithTimeout = async (
  url: string,
  options: RequestInit = {},
  timeout: number = 5000
): Promise<Response> => {
  const controller = new AbortController();
  const { signal } = controller;
  
  // Create a timeout that will abort the fetch
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, { ...options, signal });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
};

/**
 * Create a fetch request with retries
 * 
 * @param url - The URL to fetch
 * @param options - Fetch options
 * @param maxRetries - Maximum number of retries
 * @param retryDelay - Base delay between retries in milliseconds
 * @param timeout - Timeout for each attempt in milliseconds
 * @returns Promise with the fetch response
 */
export const retryFetch = async (
  url: string,
  options: RequestInit = {},
  maxRetries: number = 3,
  retryDelay: number = 1000,
  timeout: number = 5000
): Promise<Response> => {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      // Use fetchWithTimeout for each attempt
      return await fetchWithTimeout(url, options, timeout);
    } catch (error: any) {
      lastError = error;
      console.warn(`Fetch attempt ${attempt + 1}/${maxRetries + 1} failed:`, error.message);
      
      // If this was the last attempt, throw the error
      if (attempt === maxRetries) {
        throw error;
      }
      
      // Wait before next retry with exponential backoff
      const delay = retryDelay * Math.pow(1.5, attempt);
      console.log(`Retrying in ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  // This shouldn't be reached, but TypeScript needs it
  throw lastError || new Error('Failed to fetch after retries');
};

/**
 * Check if the backend API is available
 * 
 * @param endpoint - Optional health check endpoint (defaults to '/api/v1/health')
 * @returns Promise resolving to boolean indicating if API is available
 */
export const checkApiAvailability = async (
  endpoint: string = '/api/v1/health'
): Promise<boolean> => {
  try {
    const response = await retryFetch(
      getApiUrl(endpoint),
      {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      },
      2, // 2 retries (3 attempts total)
      1000, // Start with 1 second delay
      5000 // 5 second timeout
    );
    
    return response.ok;
  } catch (error) {
    console.error('API availability check failed:', error);
    return false;
  }
}; 
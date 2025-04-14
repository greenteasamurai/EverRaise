import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { setToken } from '../utils/auth';
import { getApiUrl, handleApiError } from '../utils/api';

const LoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState(null);
  const [backendStatus, setBackendStatus] = useState('unknown');
  
  const navigate = useNavigate();
  const location = useLocation();
  
  // Parse query params to get return URL
  const params = new URLSearchParams(location.search);
  const returnTo = params.get('return_to') || '/';

  // Check backend status on component mount
  useEffect(() => {
    const checkBackendStatus = async () => {
      try {
        const response = await fetch(getApiUrl('/api'), { 
          signal: AbortSignal.timeout(3000) // 3 second timeout
        });
        setBackendStatus(response.ok ? 'online' : 'error');
      } catch (err) {
        console.error('Backend status check failed:', err);
        setBackendStatus('offline');
      }
    };
    
    checkBackendStatus();
  }, []);

  // Debug bypass function for testing
  const handleDebugLogin = () => {
    const fakeToken = "DEBUG_TOKEN_" + Math.random().toString(36).substring(2);
    setToken(fakeToken);
    console.log('Debug login activated with fake token:', fakeToken);
    navigate(returnTo);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Clear previous errors and set loading state
    setError('');
    setDebugInfo(null);
    setIsLoading(true);
    
    try {
      console.log('Attempting login with:', { email, password: '****' });
      
      // Build request details
      const apiUrl = getApiUrl('/api/v1/auth/login');
      const formData = new URLSearchParams({
        username: email, // API expects 'username' even though we use email
        password: password
      });
      
      console.log('Sending login request to:', apiUrl);
      
      // Create an AbortController for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      // Send login request with timeout
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: formData,
        signal: controller.signal
      });
      
      // Clear timeout as request completed
      clearTimeout(timeoutId);
      
      console.log('Login response status:', response.status);
      
      // Get response data
      let data;
      try {
        const text = await response.text();
        data = text ? JSON.parse(text) : {};
        console.log('Login response data:', data);
      } catch (e) {
        console.error('Error parsing response JSON:', e);
        data = { detail: 'Could not parse server response' };
      }
      
      if (response.ok) {
        if (!data.access_token) {
          throw new Error('Server response missing access token');
        }
        
        // Store the token using our auth utility
        setToken(data.access_token);
        console.log('Login successful, redirecting to:', returnTo);
        
        // Redirect to the originally requested page or dashboard
        navigate(returnTo);
      } else {
        // Handle login errors
        console.error('Login failed:', data);
        
        // Handle different error scenarios
        if (response.status === 401) {
          setError('Invalid email or password. Please try again.');
        } else if (response.status === 400) {
          setError(data?.detail || 'Invalid request. Please check your input.');
        } else if (response.status >= 500) {
          setError('Server error. Please try again later or contact support.');
        } else {
          setError(data?.detail || 'Login failed. Please try again.');
        }
        
        // Set debug info for troubleshooting
        setDebugInfo({
          status: response.status,
          statusText: response.statusText,
          url: apiUrl,
          error: data?.detail || 'Unknown error'
        });
      }
    } catch (err) {
      console.error('Login fetch error:', err);
      
      // Handle different error types
      if (err.name === 'AbortError') {
        setError('Login request timed out. Please check your connection and try again.');
      } else if (err.message.includes('Failed to fetch') || err.name === 'TypeError') {
        setError('Could not connect to the server. Please check that the backend is running.');
      } else {
        setError(`Login failed: ${err.message}`);
      }
      
      setDebugInfo({
        error: err.message,
        type: err.name,
        stack: err.stack
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
      
      {backendStatus === 'offline' && (
        <div className="bg-yellow-50 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
          Backend server appears to be offline. Please check that the server is running.
        </div>
      )}
      
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
        />
      </div>
      
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          Password
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
        />
      </div>
      
      <div>
        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
        >
          {isLoading ? 'Signing in...' : 'Sign In'}
        </button>
      </div>
      
      {/* Debug bypass button - only in development */}
      {process.env.NODE_ENV !== 'production' && (
        <div className="mt-2">
          <button
            type="button"
            onClick={handleDebugLogin}
            className="w-full flex justify-center py-2 px-4 border border-blue-300 rounded-md shadow-sm text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Debug: Skip Login (Testing Only)
          </button>
        </div>
      )}
      
      {/* Debug information section */}
      {debugInfo && (
        <div className="mt-4 p-3 border border-gray-300 rounded text-xs bg-gray-50">
          <h4 className="font-semibold mb-1">Debugging Information:</h4>
          <pre className="whitespace-pre-wrap break-all">
            {JSON.stringify(debugInfo, null, 2)}
          </pre>
        </div>
      )}
      
      {/* Default credentials hint for development */}
      {process.env.NODE_ENV !== 'production' && (
        <div className="mt-4 p-2 bg-blue-50 rounded text-xs text-blue-700">
          <p><strong>Note:</strong> Try using these default admin credentials:</p>
          <p>Email: admin@example.com</p>
          <p>Password: adminpassword</p>
        </div>
      )}
    </form>
  );
};

export default LoginForm; 
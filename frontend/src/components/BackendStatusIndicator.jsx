import React, { useEffect, useState } from 'react';
import { getApiUrl } from '../utils/api';

/**
 * Component that checks and displays the status of the backend API connection
 */
const BackendStatusIndicator = ({ 
  endpoint = '/api/v1/health', 
  minimal = false
}) => {
  const [status, setStatus] = useState('checking');

  const checkBackendStatus = async () => {
    setStatus('checking');
    try {
      const response = await fetch(getApiUrl(endpoint), { 
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        // Short timeout to prevent long waits if service is down
        signal: AbortSignal.timeout(3000)
      });
      
      if (response.ok) {
        setStatus('connected');
      } else {
        setStatus('disconnected');
      }
    } catch (error) {
      console.error('Error checking backend status:', error);
      setStatus('disconnected');
    }
  };

  useEffect(() => {
    // Check status immediately on mount
    checkBackendStatus();
  }, [endpoint]);

  const getStatusColor = () => {
    switch (status) {
      case 'connected': return 'bg-green-500';
      case 'disconnected': return 'bg-red-500';
      case 'checking': return 'bg-yellow-400';
      default: return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected': return 'API Connected';
      case 'disconnected': return 'API Offline';
      case 'checking': return 'Checking API...';
      default: return 'Unknown Status';
    }
  };

  // For login page, we use a more compact version
  if (minimal) {
    return (
      <div className="flex items-center space-x-1 text-xs">
        <div className={`h-2 w-2 rounded-full ${getStatusColor()}`} />
        <span className="text-xs text-gray-500">{getStatusText()}</span>
      </div>
    );
  }

  // Regular version for header
  return (
    <div className="flex items-center space-x-2">
      <div className={`w-2 h-2 rounded-full ${getStatusColor()}`}></div>
      <span className="text-sm text-gray-600">{getStatusText()}</span>
      <button 
        onClick={checkBackendStatus}
        className="ml-1 text-gray-500 hover:text-gray-700"
        aria-label="Check connection"
        title="Check connection"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
    </div>
  );
};

export default BackendStatusIndicator; 
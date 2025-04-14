import React, { useEffect, useState } from 'react';

interface BackendStatusIndicatorProps {
  endpoint?: string;
  pollingInterval?: number;
}

/**
 * Component that checks and displays the status of the backend API connection
 */
const BackendStatusIndicator: React.FC<BackendStatusIndicatorProps> = ({ 
  endpoint = '/api/v1/health', 
  pollingInterval = 30000 
}) => {
  const [status, setStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkBackendStatus = async () => {
    setStatus('checking');
    try {
      const response = await fetch(endpoint, { 
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
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
    
    setLastChecked(new Date());
  };

  useEffect(() => {
    // Check status immediately on mount
    checkBackendStatus();
    
    // Set up polling interval
    const intervalId = setInterval(checkBackendStatus, pollingInterval);
    
    // Clean up on unmount
    return () => clearInterval(intervalId);
  }, [endpoint, pollingInterval]);

  const getStatusColor = () => {
    switch (status) {
      case 'connected': return 'bg-green-500';
      case 'disconnected': return 'bg-red-500';
      case 'checking': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected': return 'API Connected';
      case 'disconnected': return 'API Disconnected';
      case 'checking': return 'Checking API...';
      default: return 'Unknown Status';
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex items-center space-x-2 px-3 py-1 rounded-md bg-gray-100 text-xs">
      <div className={`w-2 h-2 rounded-full ${getStatusColor()}`}></div>
      <span>{getStatusText()}</span>
      {lastChecked && (
        <span className="text-gray-500">
          (Last checked: {formatTime(lastChecked)})
        </span>
      )}
      <button 
        onClick={checkBackendStatus}
        className="ml-2 text-blue-600 hover:text-blue-800"
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
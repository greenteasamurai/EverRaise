import React, { useState, useEffect } from 'react'
// Replace authenticatedFetch with regular fetch since we don't need authentication
// import { authenticatedFetch, isAuthenticated } from '../utils/auth'
// import { useNavigate } from 'react-router-dom'

// Import our API utilities
import { getApiUrl, fetchWithTimeout, retryFetch } from '../utils/api';

// Types for integration data
interface Integration {
  id: string;
  name: string;
  description: string;
  icon: string;
  connected: boolean;
}

interface IntegrationCategory {
  id: string;
  name: string;
  integrations: Integration[];
}

// Status types for service health
interface ServiceStatus {
  isOnline: boolean;
  isChecking: boolean;
  lastChecked: Date | null;
  statusText: string;
  error?: string;  // Optional error message
}

// Interface for knowledge preview data
interface KnowledgeItem {
  id: string;
  title: string;
  preview: string;
  date: string;
  source: string;
}

interface KnowledgeSource {
  id: string;
  name: string;
  icon: string;
  status: 'error' | 'partial' | 'success';
  items: KnowledgeItem[];
  error?: string;
}

// Sample integration data (to be replaced with API data)
const integrationTypes: IntegrationCategory[] = [
  {
    id: 'email',
    name: 'Email Platforms',
    integrations: [
      {
        id: 'gmail',
        name: 'Google Gmail',
        description: 'Connect your Gmail account to analyze email communications.',
        icon: '/icons/gmail.svg',
        connected: false
      },
      {
        id: 'outlook',
        name: 'Microsoft Outlook',
        description: 'Connect your Outlook account to analyze email communications.',
        icon: '/icons/outlook.svg',
        connected: false
      }
    ]
  },
  {
    id: 'communication',
    name: 'Communication',
    integrations: [
      {
        id: 'slack',
        name: 'Slack',
        description: 'Connect your Slack workspace to analyze team communications.',
        icon: '/icons/slack.svg',
        connected: false
      },
      {
        id: 'teams',
        name: 'Microsoft Teams',
        description: 'Connect your Microsoft Teams to analyze team communications.',
        icon: '/icons/teams.svg',
        connected: false
      }
    ]
  },
  {
    id: 'collaboration',
    name: 'Collaboration',
    integrations: [
      {
        id: 'github',
        name: 'GitHub',
        description: 'Connect your GitHub repositories to analyze development activity.',
        icon: '/icons/github.svg',
        connected: false
      },
      {
        id: 'gdrive',
        name: 'Google Drive',
        description: 'Connect your Google Drive to analyze documents and files.',
        icon: '/icons/gdrive.svg',
        connected: false
      }
    ]
  }
]

const Integrations: React.FC = () => {
  const [integrations, setIntegrations] = useState(integrationTypes);
  const [activeTab, setActiveTab] = useState<'all' | 'connected'>('all');
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  // Status states for backend and Ollama
  const [backendStatus, setBackendStatus] = useState<ServiceStatus>({
    isOnline: false,
    isChecking: true,
    lastChecked: null,
    statusText: 'Checking...',
    error: undefined
  });
  const [ollamaStatus, setOllamaStatus] = useState<ServiceStatus>({
    isOnline: false,
    isChecking: true,
    lastChecked: null,
    statusText: 'Checking...',
    error: undefined
  });
  
  // Knowledge sources state
  const [knowledgeSources, setKnowledgeSources] = useState<KnowledgeSource[]>([
    {
      id: 'gmail',
      name: 'Gmail',
      icon: '/icons/gmail.svg',
      status: 'error',
      items: [],
      error: 'Not connected'
    },
    {
      id: 'slack',
      name: 'Slack',
      icon: '/icons/slack.svg',
      status: 'error',
      items: [],
      error: 'Not connected'
    },
    {
      id: 'github',
      name: 'GitHub',
      icon: '/icons/github.svg',
      status: 'error',
      items: [],
      error: 'Not connected'
    }
  ]);
  const [loadingKnowledge, setLoadingKnowledge] = useState(false);
  // const navigate = useNavigate();
  
  // Check backend and Ollama status on component mount and periodically
  useEffect(() => {
    checkBackendStatus();
    checkOllamaStatus();
    
    // Set up interval to check statuses every 30 seconds
    const intervalId = setInterval(() => {
      checkBackendStatus();
      checkOllamaStatus();
    }, 30000);
    
    // Clear interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  // Check Backend Status
  const checkBackendStatus = async () => {
    setBackendStatus(prev => ({ ...prev, isChecking: true }));
    
    try {
      // Use our retry fetch utility for more reliable connection
      const response = await retryFetch(
        getApiUrl('/api/v1/health'),
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        },
        3, // Increased from 2 to 3 (total of 4 attempts)
        1000, // Start with 1 second delay
        8000 // 8 second timeout - increased from 5000 for slower connections
      );
      
      // Always consider the backend online if we get a 200 status code response
      // Even if the database connection failed, the API is still operational
      const isOnline = response.status === 200;
      let statusText = 'Online';
      let error = undefined;
      
      if (isOnline) {
        try {
          const data = await response.json();
          statusText = data.database === 'connected' 
            ? 'Online (DB Connected)' 
            : 'Online (DB Issue)';
          
          if (data.database !== 'connected') {
            console.warn('Backend database connection issue:', data.error || 'Unknown database error');
            error = data.error || 'Database connection issue';
          }
        } catch (e) {
          console.error('Error parsing health check response:', e);
          error = 'Error parsing response';
        }
      } else {
        error = `HTTP ${response.status}`;
      }
      
      setBackendStatus({
        isOnline: isOnline, // Always true for 200 status
        isChecking: false,
        lastChecked: new Date(),
        statusText: statusText,
        error: error
      });
    } catch (error: any) {
      console.error('Backend health check failed:', error);
      
      // Try to provide a more helpful error message
      let errorMessage = 'Connection failed';
      if (error?.name === 'AbortError') {
        errorMessage = 'Connection timeout';
      } else if (error?.message) {
        errorMessage = error.message;
      }
      
      setBackendStatus({
        isOnline: false,
        isChecking: false,
        lastChecked: new Date(),
        statusText: 'Offline',
        error: errorMessage
      });
    }
  };

  // Check Ollama Status
  const checkOllamaStatus = async () => {
    setOllamaStatus(prev => ({ ...prev, isChecking: true }));
    
    try {
      let response;
      let statusText = 'Online';
      let isDirectConnection = false;
      let error: string | undefined = undefined;
      
      try {
        // First try the direct connection to Ollama
        response = await retryFetch(
          'http://localhost:11434/api/tags',
          { method: 'GET' },
          1, // 1 retry (2 attempts total)
          500, // Start with 500ms delay
          3000 // 3 second timeout
        );
        
        if (response.ok) {
          try {
            const data = await response.json();
            isDirectConnection = true;
            statusText = `Online (${data.models?.length || 0} models)`;
          } catch (e) {
            console.error('Error parsing Ollama response:', e);
            statusText = 'Online (Direct)';
          }
        } else {
          error = `HTTP ${response.status}`;
        }
      } catch (directError: any) {
        // If direct connection fails, try through the backend
        console.log('Direct Ollama connection failed, trying through backend...', directError);
        
        try {
          response = await retryFetch(
            getApiUrl('/api/v1/ollama/status'),
            {
              method: 'GET',
              headers: { 'Content-Type': 'application/json' }
            },
            1, // 1 retry (2 attempts total)
            1000, // Start with 1 second delay
            5000 // 5 second timeout
          );
          
          if (response.ok) {
            try {
              const data = await response.json();
              statusText = data.available 
                ? `Online (via API)` 
                : 'Unavailable';
            } catch (e) {
              console.error('Error parsing Ollama status response:', e);
              statusText = 'Online (via API)';
            }
          } else {
            error = `API: HTTP ${response.status}`;
          }
        } catch (apiError: any) {
          error = apiError?.name === 'AbortError' 
            ? 'Timeout connecting to API' 
            : `API Error: ${apiError.message}`;
          throw apiError; // Re-throw to be caught by the outer catch
        }
        
        // If we couldn't connect directly, store that error
        if (!error) {
          error = directError?.name === 'AbortError' 
            ? 'Timeout connecting directly' 
            : `Direct connection error: ${directError.message}`;
        }
      }
      
      // If we got a response, consider it online
      setOllamaStatus({
        isOnline: response && response.ok,
        isChecking: false,
        lastChecked: new Date(),
        statusText: statusText,
        error: error
      });
    } catch (error: any) {
      console.error('Ollama health check failed:', error);
      setOllamaStatus({
        isOnline: false,
        isChecking: false,
        lastChecked: new Date(),
        statusText: 'Offline',
        error: error?.name === 'AbortError' ? 'Timeout' : error.message
      });
    }
  };
  
  // Check Gmail connection status on component mount
  useEffect(() => {
    // Remove authentication check - app doesn't require login anymore
    // if (!isAuthenticated()) {
    //   navigate('/login');
    //   return;
    // }
    
    checkGmailStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  
  // Check if we're returning from an OAuth flow
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const gmailAuth = urlParams.get('gmail_auth');
    
    if (gmailAuth === 'success') {
      // Clear the query parameter
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
      
      // Update UI to show connected status
      updateGmailConnectionStatus(true);
      
      // Show success message
      setErrorMessage(null);
      
      // After connecting, load Gmail preview data
      loadGmailPreview();
    }
  }, []);
  
  // Update Gmail connection status in the state
  const updateGmailConnectionStatus = (connected: boolean) => {
    const updatedIntegrations = [...integrations];
    const emailCategory = updatedIntegrations.find(cat => cat.id === 'email');
    
    if (emailCategory) {
      const gmailIntegration = emailCategory.integrations.find(int => int.id === 'gmail');
      if (gmailIntegration) {
        gmailIntegration.connected = connected;
      }
    }
    
    setIntegrations(updatedIntegrations);
    
    // Also update in knowledge sources
    if (connected) {
      // If connected, try to load Gmail data
      loadGmailPreview();
    } else {
      // If disconnected, update knowledge sources state
      setKnowledgeSources(sources => sources.map(source => 
        source.id === 'gmail' 
          ? { ...source, status: 'error', items: [], error: 'Not connected' } 
          : source
      ));
    }
  };
  
  // Load Gmail preview data
  const loadGmailPreview = async () => {
    // Update knowledge sources to show loading state
    setKnowledgeSources(sources => sources.map(source => 
      source.id === 'gmail' 
        ? { ...source, status: 'partial', items: [], error: 'Loading...' } 
        : source
    ));
    
    try {
      const response = await fetch(getApiUrl('/api/v1/gmail/messages?limit=3'));
      
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data && data.length > 0) {
        // Transform Gmail data to knowledge items
        const gmailItems: KnowledgeItem[] = data.slice(0, 3).map((msg: any) => ({
          id: msg.id,
          title: msg.subject,
          preview: msg.body_text.substring(0, 100) + (msg.body_text.length > 100 ? '...' : ''),
          date: new Date(msg.date).toLocaleString(),
          source: 'gmail'
        }));
        
        // Update knowledge sources with Gmail data
        setKnowledgeSources(sources => sources.map(source => 
          source.id === 'gmail' 
            ? { ...source, status: 'success', items: gmailItems, error: undefined } 
            : source
        ));
      } else {
        setKnowledgeSources(sources => sources.map(source => 
          source.id === 'gmail' 
            ? { ...source, status: 'partial', items: [], error: 'No messages found' } 
            : source
        ));
      }
    } catch (error: any) {
      console.error('Error loading Gmail preview:', error);
      setKnowledgeSources(sources => sources.map(source => 
        source.id === 'gmail' 
          ? { ...source, status: 'error', items: [], error: error.message || 'Error loading messages' } 
          : source
      ));
    }
  };
  
  // Check Gmail connection status
  const checkGmailStatus = async () => {
    setErrorMessage(null);
    
    try {
      // Use the API URL utility to get the correct backend URL
      console.log('Making request to check Gmail status...');
      const url = getApiUrl('/api/v1/gmail/status');
      console.log('Request URL:', url);
      
      const response = await fetch(url);
      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries([...response.headers.entries()]));
      
      // If response isn't OK, get the response text for debugging
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response from API:', errorText);
        throw new Error(`API error: ${response.status} - ${errorText.substring(0, 100)}...`);
      }
      
      // Try to parse response as JSON
      const text = await response.text();
      console.log('Response text:', text);
      
      let data;
      try {
        data = JSON.parse(text);
        console.log('Parsed data:', data);
      } catch (parseError) {
        console.error('Error parsing JSON:', parseError);
        throw new Error(`Invalid JSON response: ${text.substring(0, 100)}...`);
      }
      
      updateGmailConnectionStatus(data.connected);
    } catch (error) {
      console.error('Error checking Gmail status:', error);
      // Don't show error on initial load
      // This is a status check, so we don't need to alert the user if it fails
      updateGmailConnectionStatus(false);
    }
  };
  
  // Handle Gmail connection
  const handleConnectGmail = async () => {
    setIsAuthenticating(true);
    setErrorMessage(null);
    
    try {
      // Use the API URL utility to get the correct backend URL
      console.log('Making request to authorize Gmail...');
      const url = getApiUrl('/api/v1/gmail/authorize');
      console.log('Request URL:', url);
      
      const response = await fetch(url);
      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries([...response.headers.entries()]));
      
      // If response isn't OK, get the response text for debugging
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response from API:', errorText);
        throw new Error(`API error: ${response.status} - ${errorText.substring(0, 100)}...`);
      }
      
      // Try to parse response as JSON
      const text = await response.text();
      console.log('Response text:', text);
      
      let data;
      try {
        data = JSON.parse(text);
        console.log('Parsed data:', data);
      } catch (parseError) {
        console.error('Error parsing JSON:', parseError);
        throw new Error(`Invalid JSON response: ${text.substring(0, 100)}...`);
      }
      
      // If we got an auth URL, redirect to it for Google authorization
      if (data.auth_url) {
        console.log('Redirecting to Google authorization URL:', data.auth_url);
        window.location.href = data.auth_url;
        return; // Don't update state or show alerts as we're leaving the page
      }
      
      // If we didn't get redirected, update the connection status
      updateGmailConnectionStatus(true);
    } catch (error: any) {
      console.error('Error connecting to Gmail:', error);
      setErrorMessage(error.message || 'Error connecting to Gmail. Please try again.');
      updateGmailConnectionStatus(false);
    } finally {
      setIsAuthenticating(false);
    }
  };
  
  // Handle refreshing all knowledge sources
  const refreshKnowledgeSources = async () => {
    setLoadingKnowledge(true);
    
    // Check which integrations are connected
    const emailCategory = integrations.find(cat => cat.id === 'email');
    const gmailConnected = emailCategory?.integrations.find(int => int.id === 'gmail')?.connected || false;
    
    // For now, only Gmail is implemented
    if (gmailConnected) {
      await loadGmailPreview();
    }
    
    // Mock data for Slack since it's not implemented yet
    // This would be replaced with actual API calls when Slack is implemented
    const slackItems: KnowledgeItem[] = [
      {
        id: 'slack-1',
        title: 'New feature discussion',
        preview: 'Let\'s discuss the implementation of the new dashboard...',
        date: new Date().toLocaleString(),
        source: 'slack'
      },
      {
        id: 'slack-2',
        title: 'Team standup',
        preview: 'Today we\'ll be focusing on bug fixes and performance improvements...',
        date: new Date(Date.now() - 86400000).toLocaleString(), // Yesterday
        source: 'slack'
      },
      {
        id: 'slack-3',
        title: 'Project roadmap',
        preview: 'Here\'s our planned roadmap for the next quarter...',
        date: new Date(Date.now() - 172800000).toLocaleString(), // 2 days ago
        source: 'slack'
      }
    ];
    
    // Mock data for GitHub since it's not implemented yet
    const githubItems: KnowledgeItem[] = [
      {
        id: 'github-1',
        title: 'Fix sidebar navigation bug',
        preview: 'PR #123: This fixes the sidebar navigation issue when...',
        date: new Date().toLocaleString(),
        source: 'github'
      },
      {
        id: 'github-2',
        title: 'Add new authentication provider',
        preview: 'PR #122: Implements OAuth support for GitHub...',
        date: new Date(Date.now() - 86400000).toLocaleString(), // Yesterday
        source: 'github'
      },
      {
        id: 'github-3',
        title: 'Update dependencies',
        preview: 'PR #121: Updates all dependencies to latest versions...',
        date: new Date(Date.now() - 172800000).toLocaleString(), // 2 days ago
        source: 'github'
      }
    ];
    
    // Update mock data for Slack and GitHub
    setKnowledgeSources(sources => sources.map(source => {
      if (source.id === 'slack') {
        return { ...source, status: 'partial', items: slackItems, error: 'Demo data (not connected)' };
      } else if (source.id === 'github') {
        return { ...source, status: 'partial', items: githubItems, error: 'Demo data (not connected)' };
      }
      return source;
    }));
    
    setLoadingKnowledge(false);
  };
  
  // Load knowledge sources on component mount
  useEffect(() => {
    refreshKnowledgeSources();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  
  // Handle refreshing the data from integrated sources
  const handleRefreshData = async () => {
    setRefreshing(true);
    setErrorMessage(null);
    
    try {
      // In a real app, this would make an API call to refresh data from all connected sources
      // For now, we'll just simulate a delay and success
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Show success message
      setErrorMessage("Successfully refreshed data from all connected sources.");
      
      // In a real implementation, you might also update the UI to show the latest data
    } catch (error: any) {
      console.error('Error refreshing data:', error);
      setErrorMessage(error.message || 'Error refreshing data. Please try again.');
    } finally {
      setRefreshing(false);
    }
  };
  
  // Filter integrations based on active tab
  const filteredIntegrations = activeTab === 'all' 
    ? integrations 
    : integrations.map(category => ({
        ...category,
        integrations: category.integrations.filter(int => int.connected)
      })).filter(category => category.integrations.length > 0);
  
  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Integrations</h1>
        <div className="flex space-x-4">
          {/* Status indicators for backend and Ollama */}
          <div className="flex items-center space-x-4 mr-6">
            <div className="flex flex-col">
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${
                  backendStatus.isChecking 
                    ? 'bg-yellow-400 animate-pulse' 
                    : backendStatus.isOnline 
                      ? 'bg-green-500' 
                      : 'bg-red-500'
                }`}></div>
                <div className="relative group">
                  <span className="text-sm font-medium">
                    Backend: {backendStatus.isChecking ? 'Checking...' : backendStatus.isOnline ? backendStatus.statusText : 'Offline'}
                  </span>
                  {backendStatus.error && (
                    <div className="absolute z-10 invisible group-hover:visible bg-gray-700 text-white text-xs rounded p-2 left-0 mt-2 whitespace-nowrap">
                      Error: {backendStatus.error}
                    </div>
                  )}
                </div>
              </div>
              {backendStatus.lastChecked && (
                <span className="text-xs text-gray-500 ml-5">
                  Last checked: {backendStatus.lastChecked.toLocaleTimeString()}
                </span>
              )}
            </div>
            
            <div className="flex flex-col">
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${
                  ollamaStatus.isChecking 
                    ? 'bg-yellow-400 animate-pulse' 
                    : ollamaStatus.isOnline 
                      ? 'bg-green-500' 
                      : 'bg-red-500'
                }`}></div>
                <div className="relative group">
                  <span className="text-sm font-medium">
                    Ollama: {ollamaStatus.isChecking ? 'Checking...' : ollamaStatus.isOnline ? ollamaStatus.statusText : 'Offline'}
                  </span>
                  {ollamaStatus.error && (
                    <div className="absolute z-10 invisible group-hover:visible bg-gray-700 text-white text-xs rounded p-2 left-0 mt-2 whitespace-nowrap">
                      Error: {ollamaStatus.error}
                    </div>
                  )}
                </div>
              </div>
              {ollamaStatus.lastChecked && (
                <span className="text-xs text-gray-500 ml-5">
                  Last checked: {ollamaStatus.lastChecked.toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>

          <button 
            className={`px-4 py-2 rounded ${activeTab === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setActiveTab('all')}
          >
            All
          </button>
          <button 
            className={`px-4 py-2 rounded ${activeTab === 'connected' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setActiveTab('connected')}
          >
            Connected
          </button>
          <button 
            className="px-4 py-2 rounded bg-green-600 text-white flex items-center"
            onClick={handleRefreshData}
            disabled={refreshing}
          >
            {refreshing ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Refreshing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                Refresh Data
              </>
            )}
          </button>
        </div>
      </div>
      
      {/* Manual refresh button for service status */}
      <div className="mb-4 flex justify-end">
        <button 
          onClick={() => {
            checkBackendStatus();
            checkOllamaStatus();
          }}
          className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
        >
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
          Refresh Service Status
        </button>
      </div>
      
      {errorMessage && (
        <div className={`mb-4 p-3 border rounded ${errorMessage.includes('Error') ? 'bg-red-100 border-red-400 text-red-700' : 'bg-green-100 border-green-400 text-green-700'}`}>
          {errorMessage}
        </div>
      )}
      
      {filteredIntegrations.map(category => (
        <div key={category.id} className="mb-8">
          <h2 className="text-xl font-semibold mb-4">{category.name}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {category.integrations.map(integration => (
              <div key={integration.id} className="border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center mb-3">
                  <div className="w-10 h-10 mr-3">
                    <img src={integration.icon} alt={integration.name} className="w-full h-full object-contain" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold">{integration.name}</h3>
                    <div className={`text-xs px-2 py-1 rounded-full inline-block ${integration.connected ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {integration.connected ? 'Connected' : 'Not Connected'}
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-3">{integration.description}</p>
                {integration.id === 'gmail' ? (
                  <button
                    onClick={integration.connected ? () => {} : handleConnectGmail}
                    disabled={isAuthenticating || (integration.connected && true)}
                    className={`w-full py-2 px-4 rounded text-sm font-medium ${
                      integration.connected 
                        ? 'bg-gray-100 text-gray-500 cursor-not-allowed' 
                        : isAuthenticating
                          ? 'bg-blue-400 text-white cursor-wait'
                          : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                  >
                    {isAuthenticating ? 'Connecting...' : integration.connected ? 'Connected' : 'Connect'}
                  </button>
                ) : (
                  <button
                    // For other integrations, this would trigger a different connect function
                    // For now, it's just a placeholder
                    className="w-full py-2 px-4 rounded text-sm font-medium bg-blue-600 text-white hover:bg-blue-700"
                    onClick={() => {}}
                  >
                    Connect
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
      
      {filteredIntegrations.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No integrations found. Try changing the filter.
        </div>
      )}
      
      {/* New Knowledge Summary section */}
      <div className="mt-12 mb-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Knowledge Summary</h2>
          <button 
            className={`px-4 py-2 rounded bg-green-600 text-white flex items-center ${loadingKnowledge ? 'opacity-75 cursor-wait' : ''}`}
            onClick={refreshKnowledgeSources}
            disabled={loadingKnowledge}
          >
            {loadingKnowledge ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Refreshing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                Refresh Knowledge
              </>
            )}
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {knowledgeSources.map(source => (
            <div key={source.id} className="border rounded-lg shadow-sm overflow-hidden">
              {/* Header with icon and status indicator */}
              <div className="flex items-center justify-between p-4 bg-gray-50 border-b">
                <div className="flex items-center">
                  <div className="w-8 h-8 mr-3">
                    <img src={source.icon} alt={source.name} className="w-full h-full object-contain" />
                  </div>
                  <h3 className="font-semibold">{source.name}</h3>
                </div>
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded-full ${
                    source.status === 'success' ? 'bg-green-500' :
                    source.status === 'partial' ? 'bg-yellow-500' :
                    'bg-red-500'
                  }`}></div>
                </div>
              </div>
              
              {/* Content area */}
              <div className="p-4">
                {source.items.length > 0 ? (
                  <div className="space-y-4">
                    {source.items.map(item => (
                      <div key={item.id} className="border-b pb-3 last:border-b-0 last:pb-0">
                        <h4 className="font-medium text-gray-900">{item.title}</h4>
                        <p className="text-sm text-gray-600 my-1">{item.preview}</p>
                        <div className="text-xs text-gray-500">{item.date}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    {source.error || 'No data available'}
                  </div>
                )}
              </div>
              
              {/* Footer with status message */}
              {source.error && (
                <div className={`px-4 py-2 text-xs ${
                  source.status === 'success' ? 'bg-green-100 text-green-800' :
                  source.status === 'partial' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {source.error}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Integrations; 
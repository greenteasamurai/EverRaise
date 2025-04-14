import React, { useState } from 'react';
import SystemDiagnostics from '../components/SystemDiagnostics';
import LLMStatusIndicator from '../components/LLMStatusIndicator';
import BackendStatusIndicator from '../components/BackendStatusIndicator';
import { isAuthenticated } from '../utils/auth';

const SystemStatus = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const userIsAuthenticated = isAuthenticated();

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">System Status</h1>
        <p className="text-gray-600">
          View the current status of system components and integrations
        </p>
      </div>

      {/* Tab navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            className={`
              py-4 px-1 border-b-2 font-medium text-sm
              ${activeTab === 'overview' 
                ? 'border-primary text-primary' 
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
            `}
            onClick={() => setActiveTab('overview')}
          >
            System Overview
          </button>
          <button
            className={`
              py-4 px-1 border-b-2 font-medium text-sm
              ${activeTab === 'integrations' 
                ? 'border-primary text-primary' 
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
            `}
            onClick={() => setActiveTab('integrations')}
          >
            Integrations
          </button>
          {userIsAuthenticated && (
            <button
              className={`
                py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === 'advanced' 
                  ? 'border-primary text-primary' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
              `}
              onClick={() => setActiveTab('advanced')}
            >
              Advanced Diagnostics
            </button>
          )}
        </nav>
      </div>

      {/* Content based on active tab */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <>
            <div className="grid grid-cols-1 gap-6">
              {/* System Diagnostics Component */}
              <SystemDiagnostics />

              {/* Quick Help Section */}
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="text-lg font-medium mb-4">Common Issues</h3>
                
                <div className="space-y-4">
                  <div className="p-3 bg-blue-50 rounded-md">
                    <h4 className="font-medium text-blue-800 mb-1">Database Connection Issues</h4>
                    <p className="text-sm text-blue-700">
                      If the database is showing as disconnected, check that your database server is running
                      and the application has proper credentials.
                    </p>
                  </div>
                  
                  <div className="p-3 bg-blue-50 rounded-md">
                    <h4 className="font-medium text-blue-800 mb-1">LLM Service (Ollama) Offline</h4>
                    <p className="text-sm text-blue-700">
                      If Ollama is showing as disconnected, ensure that the Ollama service is running.
                      <br />
                      <code className="bg-blue-100 px-1 py-0.5 rounded text-xs">
                        Run: ollama serve
                      </code>
                    </p>
                  </div>
                  
                  <div className="p-3 bg-blue-50 rounded-md">
                    <h4 className="font-medium text-blue-800 mb-1">Gmail Authentication Required</h4>
                    <p className="text-sm text-blue-700">
                      If Gmail shows "Authentication Required", you need to authenticate with Gmail to use this integration.
                      Visit the Integrations tab to set up authentication.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'integrations' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h3 className="text-lg font-medium">Integrations Status</h3>
              <p className="text-sm text-gray-500">
                Check the status of each integration and configure connections.
              </p>
            </div>

            {/* Integration cards */}
            <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="border rounded-lg p-4">
                <h4 className="text-lg font-medium mb-2">Ollama LLM</h4>
                <p className="text-sm text-gray-600 mb-4">
                  Local AI model for report generation and analysis. 
                </p>
                <div className="space-y-2">
                  <div className="text-sm">
                    <span className="font-medium">Status:</span> <LLMStatusIndicator />
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">Server:</span> localhost:11434
                  </div>
                  
                  <div className="flex mt-4">
                    <button className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                      Test Connection
                    </button>
                  </div>
                </div>
              </div>

              <div className="border rounded-lg p-4">
                <h4 className="text-lg font-medium mb-2">Gmail Integration</h4>
                <p className="text-sm text-gray-600 mb-4">
                  Connect to Gmail to analyze email communications.
                </p>
                <div className="space-y-2">
                  <div className="text-sm">
                    <span className="font-medium">Status:</span> <span className="text-red-600">Auth Required</span>
                  </div>
                  
                  <div className="flex mt-4">
                    <button className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                      Authenticate
                    </button>
                  </div>
                </div>
              </div>

              <div className="border rounded-lg p-4">
                <h4 className="text-lg font-medium mb-2">Database</h4>
                <p className="text-sm text-gray-600 mb-4">
                  SQLite database for storing user data and reports.
                </p>
                <div className="space-y-2">
                  <div className="text-sm">
                    <span className="font-medium">Status:</span> <BackendStatusIndicator />
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">Type:</span> SQLite
                  </div>
                  
                  <div className="flex mt-4">
                    <button className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                      View Details
                    </button>
                  </div>
                </div>
              </div>

              <div className="border rounded-lg p-4 opacity-50">
                <h4 className="text-lg font-medium mb-2">Redis (Optional)</h4>
                <p className="text-sm text-gray-600 mb-4">
                  In-memory cache for improved performance (not configured).
                </p>
                <div className="space-y-2">
                  <div className="text-sm">
                    <span className="font-medium">Status:</span> <span className="text-gray-600">Not Configured</span>
                  </div>
                  
                  <div className="flex mt-4">
                    <button className="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded" disabled>
                      Configure
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'advanced' && userIsAuthenticated && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b">
                <h3 className="text-lg font-medium">Advanced System Diagnostics</h3>
                <p className="text-sm text-gray-500">
                  Detailed system information for administrators. This data requires authentication.
                </p>
              </div>
              <div className="p-4">
                <SystemDiagnostics requireAuth={true} />
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-lg font-medium mb-4">System Actions</h3>
              <div className="space-y-4">
                <div className="p-3 border rounded-md">
                  <h4 className="font-medium mb-2">Reset Database Connection</h4>
                  <p className="text-sm text-gray-600 mb-3">
                    Attempt to reset the database connection pool. Use this if you're experiencing database connectivity issues.
                  </p>
                  <button className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                    Reset Connection
                  </button>
                </div>
                
                <div className="p-3 border rounded-md">
                  <h4 className="font-medium mb-2">Clear Redis Cache</h4>
                  <p className="text-sm text-gray-600 mb-3">
                    Clear the Redis cache to reset all cached data. This may temporarily reduce performance.
                  </p>
                  <button className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700" disabled>
                    Clear Cache
                  </button>
                </div>
                
                <div className="p-3 border border-red-200 rounded-md">
                  <h4 className="font-medium text-red-600 mb-2">Restart Application</h4>
                  <p className="text-sm text-gray-600 mb-3">
                    Request a restart of the application server. This will temporarily disrupt service.
                  </p>
                  <button className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700">
                    Restart Application
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemStatus; 
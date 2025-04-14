import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
// Import the getApiUrl function from API utilities
import { getApiUrl, fetchWithTimeout } from '../utils/api';
import { authenticatedFetch } from '../utils/auth';

// Sample data for demonstration
const reportTypes = [
  {
    id: "investor_update",
    name: "Investor Update",
    description: "Generate an investor update with key metrics, progress, and funding needs"
  },
  {
    id: "weekly_ops",
    name: "Weekly Ops Report",
    description: "Detailed operational report with team progress, blockers, and next steps"
  },
  {
    id: "meetings_tasks",
    name: "Weekly Meetings/Reminders/Tasks",
    description: "Summary of scheduled meetings, upcoming deadlines, and pending tasks"
  }
];

const dataSources = [
  {
    id: "gmail",
    name: "Gmail",
    description: "Email messages from Gmail",
    status: "available",
    isConnected: true
  },
  {
    id: "slack",
    name: "Slack",
    description: "Messages and channels from Slack",
    status: "coming_soon",
    isConnected: false
  },
  {
    id: "github",
    name: "GitHub",
    description: "Pull requests, issues, and commits",
    status: "available",
    isConnected: true
  },
  {
    id: "gdrive",
    name: "Google Drive",
    description: "Documents and files from Google Drive",
    status: "available",
    isConnected: false
  }
];

const aiModels = [
  {
    id: "openai",
    name: "OpenAI GPT-4",
    description: "Powerful language model from OpenAI",
    models: ["gpt-4", "gpt-3.5-turbo"]
  },
  {
    id: "gemini",
    name: "Google Gemini",
    description: "Google's advanced language model",
    models: ["gemini-pro", "gemini-ultra"]
  },
  {
    id: "ollama",
    name: "Ollama",
    description: "Open-source local language model",
    models: ["llama2", "mistral", "mixtral"]
  }
];

const ReportGeneration: React.FC = () => {
  const navigate = useNavigate();
  const [reportTitle, setReportTitle] = useState('');
  const [reportType, setReportType] = useState('');
  const [timePeriod, setTimePeriod] = useState('last_7_days');
  const [customRange, setCustomRange] = useState({ start: '', end: '' });
  const [selectedDataSources, setSelectedDataSources] = useState<string[]>([]);
  const [aiProvider, setAiProvider] = useState('ollama');
  const [aiModel, setAiModel] = useState('');
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [primaryPrompt, setPrimaryPrompt] = useState('');
  const [secondaryPrompts, setSecondaryPrompts] = useState<string[]>(['']);
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showError, setShowError] = useState(false);
  const [ollamaStatus, setOllamaStatus] = useState<'unknown' | 'available' | 'unavailable'>('unknown');

  // Check Ollama status on load
  useEffect(() => {
    checkOllamaStatus();
  }, []);

  const checkOllamaStatus = async () => {
    try {
      const response = await fetchWithTimeout(
        getApiUrl('/api/v1/diagnostics/ollama/status'),
        {
          method: 'GET',
        },
        5000 // 5 second timeout
      );

      // Parse the response - fetchWithTimeout already returns the parsed JSON
      const data = response as unknown as {
        available: boolean;
        default_model_available: boolean;
        default_model: string;
        models: string[];
      };

      if (data && data.available) {
        setOllamaStatus('available');
        
        // Set default AI model if available
        if (data.default_model_available && data.default_model) {
          const modelProvider = aiModels.find(p => p.models.includes(data.default_model));
          if (modelProvider) {
            setAiProvider(modelProvider.id);
            setAiModel(data.default_model);
          }
        }
      } else {
        setOllamaStatus('unavailable');
        showErrorMessage('LLM service is not available. Some features may be limited.');
      }
    } catch (error) {
      console.error('Error checking Ollama status:', error);
      setOllamaStatus('unavailable');
    }
  };

  useEffect(() => {
    if (showError) {
      const timer = setTimeout(() => {
        setShowError(false);
      }, 8000); // Show error for 8 seconds instead of 5
      return () => clearTimeout(timer);
    }
  }, [showError]);
  
  const handleSourceToggle = (sourceId: string) => {
    if (selectedDataSources.includes(sourceId)) {
      setSelectedDataSources(selectedDataSources.filter(id => id !== sourceId));
    } else {
      setSelectedDataSources([...selectedDataSources, sourceId]);
    }
  };
  
  const showErrorMessage = (message: string) => {
    setErrorMessage(message);
    setShowError(true);
  };
  
  // Generate a new report
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);
    setErrorMessage(null);
    setShowError(false);
    
    if (!reportTitle || !reportType || selectedDataSources.length === 0) {
      showErrorMessage('Please fill in all required fields');
      setIsGenerating(false);
      return;
    }
    
    // Validate data before submitting
    if (ollamaStatus === 'unavailable') {
      showErrorMessage('LLM service is not available. Please check the Ollama connection and try again.');
      setIsGenerating(false);
      return;
    }
    
    // Create the report request payload
    const reportRequest = {
      title: reportTitle,
      report_type: reportType,
      time_period: timePeriod,
      data_sources: selectedDataSources,
      primary_prompt: primaryPrompt || undefined,
      secondary_prompts: secondaryPrompts.filter(p => p.trim() !== '') || undefined
    };
    
    console.log('Submitting report request:', reportRequest);
    
    try {
      // Make the actual API call to generate the report using authenticatedFetch
      // Increased timeout to 90 seconds for larger reports
      const response = await authenticatedFetch(
        getApiUrl('/api/v1/reports/generate'),
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(reportRequest),
        },
        90000 // 90 second timeout
      );
      
      // authenticatedFetch already parses JSON
      const data = response;
      console.log('Report generation response:', data);
      
      if (data && data.id) {
        // Check for immediate errors in the response
        if (data.status === 'error' || data.status === 'failed') {
          throw new Error(data.error_message || 'Report generation failed');
        }
        
        // Redirect to the reports page with a success message
        navigate('/reports', { 
          state: { 
            message: 'Report generation started successfully!',
            reportId: data.id
          } 
        });
      } else {
        // Handle API error
        let errorMessage = 'Unknown error occurred';
        
        if (data?.detail) {
          if (typeof data.detail === 'object') {
            errorMessage = data.detail.error || data.detail.message || JSON.stringify(data.detail);
          } else {
            errorMessage = data.detail;
          }
        }
        
        // Provide more helpful error messages
        if (errorMessage.includes('timeout')) {
          errorMessage = 'The request timed out. The AI model may be taking too long to respond. Please try again or use a simpler report type.';
        } else if (errorMessage.includes('connect')) {
          errorMessage = 'Could not connect to the AI service. Please ensure Ollama is running and try again.';
        } else if (errorMessage.includes('redis')) {
          errorMessage = 'Could not queue the report generation task. Please verify that the backend queue service is running.';
        }
        
        throw new Error(errorMessage);
      }
    } catch (error: any) {
      console.error('Error generating report:', error);
      
      // Create a more user-friendly error message
      let errorMessage = 'An error occurred while generating the report.';
      
      if (error.name === 'AbortError') {
        errorMessage = 'The request timed out. This usually happens when the report generation takes too long. Your report may still be generating in the background - please check the Reports page in a few minutes.';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      // Handle specific error codes
      if (error.status === 401 || error.status === 403) {
        errorMessage = 'You do not have permission to generate this report. Please log in again or contact support.';
      } else if (error.status === 404) {
        errorMessage = 'The report generation service could not be found. Please verify that the backend is running.';
      } else if (error.status === 500) {
        errorMessage = 'The server encountered an error while processing your request. Our team has been notified.';
      } else if (error.status === 503) {
        errorMessage = 'The report generation service is currently unavailable. Please try again later.';
      }
      
      showErrorMessage(errorMessage);
      
      // Check if Ollama is still available
      checkOllamaStatus();
    } finally {
      setIsGenerating(false);
    }
  };
  
  // Get available models for the selected AI provider
  const getAvailableModels = () => {
    const provider = aiModels.find(p => p.id === aiProvider);
    return provider ? provider.models : [];
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Report Generation</h1>
        
        {/* Ollama Status Indicator */}
        <div className="flex items-center">
          <span className="mr-2">LLM Service:</span>
          {ollamaStatus === 'available' ? (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
              Available
            </span>
          ) : ollamaStatus === 'unavailable' ? (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
              <span className="w-2 h-2 bg-red-500 rounded-full mr-1"></span>
              Unavailable
            </span>
          ) : (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
              <span className="w-2 h-2 bg-gray-500 rounded-full mr-1"></span>
              Checking...
            </span>
          )}
          <button 
            onClick={checkOllamaStatus} 
            className="ml-2 text-sm text-blue-600 hover:text-blue-800"
            title="Check LLM service status"
          >
            Refresh
          </button>
        </div>
      </div>
      
      {errorMessage && showError && (
        <div className="mb-4 p-4 bg-red-100 border-l-4 border-red-500 text-red-700 rounded flex justify-between items-start">
          <div>{errorMessage}</div>
          <button 
            onClick={() => setShowError(false)} 
            className="text-red-700 hover:text-red-900"
          >
            ×
          </button>
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Create New Report</h2>
        
        <div className="grid grid-cols-1 gap-y-6">
          {/* Report Title */}
          <div>
            <label htmlFor="reportTitle" className="block text-sm font-medium text-gray-700 mb-1">
              Report Title *
            </label>
            <input
              type="text"
              id="reportTitle"
              className="w-full p-2 border rounded"
              value={reportTitle}
              onChange={(e) => setReportTitle(e.target.value)}
              placeholder="Enter a title for your report"
            />
          </div>
          
          {/* Report Type */}
          <div>
            <label htmlFor="reportType" className="block text-sm font-medium text-gray-700 mb-1">
              Report Type *
            </label>
            <select
              id="reportType"
              className="w-full p-2 border rounded"
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
            >
              <option value="">Select a report type</option>
              {reportTypes.map(type => (
                <option key={type.id} value={type.id}>
                  {type.name}
                </option>
              ))}
            </select>
          </div>
          
          {/* Time Period */}
          <div>
            <label htmlFor="timePeriod" className="block text-sm font-medium text-gray-700 mb-1">
              Time Period
            </label>
            <select
              id="timePeriod"
              className="w-full p-2 border rounded"
              value={timePeriod}
              onChange={(e) => setTimePeriod(e.target.value)}
            >
              <option value="last_7_days">Last 7 Days</option>
              <option value="last_14_days">Last 14 Days</option>
              <option value="last_30_days">Last 30 Days</option>
              <option value="last_90_days">Last 90 Days</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>
          
          {/* Data Sources */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data Sources *
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {dataSources.map(source => (
                <div
                  key={source.id}
                  className={`border rounded-lg p-3 ${
                    !source.isConnected ? 'opacity-50 cursor-not-allowed' : 
                    selectedDataSources.includes(source.id) ? 'border-blue-500 bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id={`source-${source.id}`}
                      checked={selectedDataSources.includes(source.id)}
                      onChange={() => source.isConnected && handleSourceToggle(source.id)}
                      disabled={!source.isConnected}
                      className="mr-2"
                    />
                    <label htmlFor={`source-${source.id}`} className="flex items-center cursor-pointer">
                      <span className="font-medium">{source.name}</span>
                      {!source.isConnected && (
                        <span className="ml-2 text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                          Not Connected
                        </span>
                      )}
                    </label>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{source.description}</p>
                </div>
              ))}
            </div>
          </div>
          
          {/* AI Provider */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              AI Provider
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
              {aiModels.map(provider => (
                <div
                  key={provider.id}
                  className={`border rounded-lg p-3 cursor-pointer ${
                    aiProvider === provider.id ? 'border-blue-500 bg-blue-50' : ''
                  } ${provider.id === 'ollama' && ollamaStatus !== 'available' ? 'opacity-50 cursor-not-allowed' : ''}`}
                  onClick={() => {
                    if (!(provider.id === 'ollama' && ollamaStatus !== 'available')) {
                      setAiProvider(provider.id);
                    }
                  }}
                >
                  <div className="flex items-center justify-between">
                    <label className="font-medium cursor-pointer">
                      {provider.name}
                    </label>
                    {provider.id === 'ollama' && ollamaStatus !== 'available' && (
                      <span className="ml-2 text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                        Unavailable
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{provider.description}</p>
                </div>
              ))}
            </div>
          </div>
          
          {/* AI Model */}
          <div>
            <label htmlFor="aiModel" className="block text-sm font-medium text-gray-700 mb-1">
              AI Model
            </label>
            <select
              id="aiModel"
              className="w-full p-2 border rounded"
              value={aiModel}
              onChange={(e) => setAiModel(e.target.value)}
            >
              <option value="">Select model</option>
              {getAvailableModels().map(model => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </div>
          
          {/* Advanced Options Toggle */}
          <div>
            <button
              type="button"
              className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
              onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
            >
              {showAdvancedOptions ? (
                <>
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7" />
                  </svg>
                  Hide Advanced Options
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                  </svg>
                  Show Advanced Options
                </>
              )}
            </button>
          </div>
          
          {/* Advanced Options */}
          {showAdvancedOptions && (
            <>
              <div>
                <label htmlFor="primaryPrompt" className="block text-sm font-medium text-gray-700 mb-1">
                  Primary Prompt
                </label>
                <textarea
                  id="primaryPrompt"
                  className="w-full p-2 border rounded"
                  rows={4}
                  value={primaryPrompt}
                  onChange={(e) => setPrimaryPrompt(e.target.value)}
                />
              </div>
            </>
          )}
          
          {/* Generate Button */}
          <div className="mt-4">
            <button
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium disabled:bg-blue-300"
              onClick={handleSubmit}
              disabled={isGenerating || !reportTitle || !reportType || selectedDataSources.length === 0}
            >
              {isGenerating ? (
                <div className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Generating Report...
                </div>
              ) : (
                'Generate Report'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportGeneration; 
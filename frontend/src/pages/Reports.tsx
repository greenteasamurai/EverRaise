import React, { useState, useEffect, useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom';
// Import the getApiUrl function from API utilities
import { getApiUrl } from '../utils/api';
import { authenticatedFetch } from '../utils/auth';

// Define the Report type
interface Report {
  id: number;
  name: string;
  type: string;
  description: string;
  generated: string;
  status: 'processing' | 'complete';
}

// Sample data for demonstration
const reportTypes = [
  {
    id: "investor_update",
    name: "Investor Update",
    description: "Generate an investor update with key metrics, progress, and funding needs"
  },
  {
    id: "knowledge_summary",
    name: "Knowledge Summary",
    description: "Summarize key information from multiple sources"
  },
  {
    id: "weekly_ops",
    name: "Weekly Ops Report",
    description: "Detailed operational report with team progress, blockers, and next steps"
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

// Sample reports data
const existingReports = [
  { 
    id: 1, 
    name: "Q2 Fundraising Overview",
    type: "investor_update",
    description: "Summary of fundraising activities and investor relations for Q2",
    generated: "2023-06-30",
    status: "complete"
  },
  { 
    id: 2, 
    name: "Donor Retention Analysis",
    type: "knowledge_summary",
    description: "Analysis of donor retention rates and strategies for improvement",
    generated: "2023-05-15",
    status: "complete"
  },
  { 
    id: 3, 
    name: "Campaign Performance",
    type: "weekly_ops",
    description: "Review of marketing campaign effectiveness and ROI",
    generated: "2023-07-10",
    status: "complete"
  },
  { 
    id: 4, 
    name: "Weekly Team Update",
    type: "weekly_ops",
    description: "Summary of team activities, blockers, and priorities",
    generated: "2023-07-12",
    status: "complete"
  },
  { 
    id: 5, 
    name: "Product Roadmap Review",
    type: "weekly_ops",
    description: "Analysis of product development progress against roadmap",
    generated: "2023-07-05",
    status: "complete"
  }
];

// Sample AI providers
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

// Report cache to store report data from the API
const reportCacheInitial: Record<string, any> = {};

const Reports: React.FC = () => {
  const location = useLocation();
  const [activeTab, setActiveTab] = useState('all');
  const [reports, setReports] = useState<Report[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [pollingReportIds, setPollingReportIds] = useState<number[]>([]);
  const [message, setMessage] = useState<string | null>(location.state?.message || null);
  const [showMessage, setShowMessage] = useState<boolean>(!!location.state?.message);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // Modal state for new report creation
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [reportTitle, setReportTitle] = useState('');
  const [reportType, setReportType] = useState('');
  const [timePeriod, setTimePeriod] = useState('last_7_days');
  const [queryFilter, setQueryFilter] = useState('');
  const [primaryPrompt, setPrimaryPrompt] = useState('');
  const [secondaryPrompts, setSecondaryPrompts] = useState<string[]>(['']);
  const [selectedDataSources, setSelectedDataSources] = useState<string[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Load reports on initial render
  useEffect(() => {
    fetchReports();
    
    // Check if we need to focus on a specific report from the redirect
    if (location.state?.reportId) {
      const reportId = parseInt(location.state.reportId);
      if (!isNaN(reportId)) {
        setPollingReportIds(prev => [...prev, reportId]);
      }
    }
    
    // Clear the location state to prevent showing the message on refresh
    window.history.replaceState({}, document.title);
  }, []);
  
  // Set up polling for reports that are being generated
  useEffect(() => {
    if (pollingReportIds.length === 0) return;
    
    const pollInterval = setInterval(() => {
      pollReportStatus();
    }, 5000); // Poll every 5 seconds
    
    return () => clearInterval(pollInterval);
  }, [pollingReportIds, reports]);
  
  // Poll for status updates on reports being generated
  const pollReportStatus = async () => {
    if (pollingReportIds.length === 0) return;
    
    try {
      const updatedReports = [...reports];
      let shouldUpdateReports = false;
      let completedReportIds: number[] = [];
      
      for (const reportId of pollingReportIds) {
        try {
          const response = await authenticatedFetch(
            getApiUrl(`/api/v1/reports/${reportId}`),
            { method: 'GET' },
            10000 // 10 second timeout
          );
          
          if (response) {
            const reportIndex = updatedReports.findIndex(r => r.id === reportId);
            
            if (reportIndex !== -1) {
              // Update existing report
              updatedReports[reportIndex] = {
                ...updatedReports[reportIndex],
                status: response.status === 'completed' || response.status === 'published' ? 'complete' : 'processing'
              };
              shouldUpdateReports = true;
              
              // If report is complete or failed, stop polling for it
              if (response.status === 'completed' || response.status === 'published' || response.status === 'failed') {
                completedReportIds.push(reportId);
                
                // Show message for newly completed reports
                if (response.status === 'completed' || response.status === 'published') {
                  setMessage(`Report "${response.title}" has been completed!`);
                  setShowMessage(true);
                } else if (response.status === 'failed') {
                  setErrorMessage(`Report "${response.title}" failed to generate. Please check the logs or try again.`);
                }
              }
            }
          }
        } catch (error) {
          console.error(`Error polling report ${reportId}:`, error);
        }
      }
      
      // Update reports if any changes were made
      if (shouldUpdateReports) {
        setReports(updatedReports);
      }
      
      // Remove completed reports from polling
      if (completedReportIds.length > 0) {
        setPollingReportIds(prev => prev.filter(id => !completedReportIds.includes(id)));
      }
    } catch (error) {
      console.error('Error polling reports:', error);
    }
  };
  
  // Fetch all reports
  const fetchReports = async () => {
    setIsLoading(true);
    try {
      const response = await authenticatedFetch(
        getApiUrl('/api/v1/reports'),
        { method: 'GET' },
        10000 // 10 second timeout
      );
      
      if (response && Array.isArray(response)) {
        const formattedReports: Report[] = response.map(r => ({
          id: r.id,
          name: r.title,
          type: r.report_type,
          description: r.description || `${r.report_type} report`,
          generated: new Date(r.created_at).toISOString().split('T')[0],
          status: (r.status === 'completed' || r.status === 'published') ? 'complete' : 'processing'
        }));
        
        setReports(formattedReports);
        
        // Start polling for in-progress reports
        const reportsToWatch = response
          .filter(r => r.status === 'pending' || r.status === 'generating')
          .map(r => r.id);
        
        if (reportsToWatch.length > 0) {
          setPollingReportIds(reportsToWatch);
        }
      }
    } catch (error) {
      console.error('Error fetching reports:', error);
      setErrorMessage('Could not load reports. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Filter reports based on active tab
  const filteredReports = useMemo(() => {
    if (activeTab === 'all') return reports;
    return reports.filter(report => report.type === activeTab);
  }, [reports, activeTab]);
  
  // Handle data source toggle
  const handleSourceToggle = (sourceId: string) => {
    if (selectedDataSources.includes(sourceId)) {
      setSelectedDataSources(selectedDataSources.filter(id => id !== sourceId));
    } else {
      setSelectedDataSources([...selectedDataSources, sourceId]);
    }
  };
  
  // Add secondary prompt field
  const addSecondaryPrompt = () => {
    setSecondaryPrompts([...secondaryPrompts, '']);
  };
  
  // Update secondary prompt
  const updateSecondaryPrompt = (index: number, value: string) => {
    const updatedPrompts = [...secondaryPrompts];
    updatedPrompts[index] = value;
    setSecondaryPrompts(updatedPrompts);
  };
  
  // Remove secondary prompt
  const removeSecondaryPrompt = (index: number) => {
    setSecondaryPrompts(secondaryPrompts.filter((_, i) => i !== index));
  };
  
  // Show error message
  const showErrorMessage = (message: string) => {
    setErrorMessage(message);
    // Auto-hide after 8 seconds
    setTimeout(() => setErrorMessage(null), 8000);
  };
  
  // Submit report generation
  const handleSubmitReport = async () => {
    if (!reportTitle || !reportType || selectedDataSources.length === 0) {
      showErrorMessage('Please fill in all required fields');
      return;
    }
    
    setIsGenerating(true);
    
    // Add a processing report immediately to the UI
    const newReportId = reports.length ? Math.max(...reports.map(r => r.id)) + 1 : 1;
    const newReport: Report = {
      id: newReportId,
      name: reportTitle,
      type: reportType,
      description: `${reportTitle} - Generated from ${selectedDataSources.join(', ')}`,
      generated: new Date().toISOString().split('T')[0],
      status: 'processing'
    };
    
    setReports([newReport, ...reports]);
    setIsModalOpen(false);
    
    // Prepare the report generation request
    const reportRequest = {
      title: reportTitle,
      report_type: reportType,
      time_period: timePeriod,
      data_sources: selectedDataSources,
      query_filter: queryFilter || undefined,
      primary_prompt: primaryPrompt || undefined,
      secondary_prompts: secondaryPrompts.filter(prompt => prompt.trim() !== '')
    };
    
    try {
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
      
      if (response && response.id) {
        // Update the UI with the actual report ID from the response
        setReports(prev => prev.map(r => 
          r.id === newReportId ? { ...r, id: response.id } : r
        ));
        
        // Add the new report ID to the polling list
        setPollingReportIds(prev => [...prev, response.id]);
        
        // Show success message
        setMessage('Report generation started successfully!');
        setShowMessage(true);
      } else {
        // Handle API error
        showErrorMessage('Failed to start report generation. Please try again.');
        // Remove the optimistically added report
        setReports(prev => prev.filter(r => r.id !== newReportId));
      }
    } catch (error: any) {
      console.error('Error generating report:', error);
      
      // Create a user-friendly error message
      let errorMessage = 'An error occurred while generating the report.';
      
      if (error.name === 'AbortError') {
        errorMessage = 'The request timed out. Your report may still be generating. Please check back later.';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      showErrorMessage(errorMessage);
      
      // Remove the optimistically added report
      setReports(prev => prev.filter(r => r.id !== newReportId));
    } finally {
      setIsGenerating(false);
      
      // Reset form
      setReportTitle('');
      setReportType('');
      setTimePeriod('last_7_days');
      setSelectedDataSources([]);
      setQueryFilter('');
      setPrimaryPrompt('');
      setSecondaryPrompts(['']);
    }
  };
  
  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Reports</h1>
        <div className="flex space-x-4">
          <button 
            className={`px-4 py-2 rounded ${activeTab === 'investor_update' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setActiveTab('investor_update')}
          >
            Investor Updates
          </button>
          <button 
            className={`px-4 py-2 rounded ${activeTab === 'knowledge_summary' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setActiveTab('knowledge_summary')}
          >
            Knowledge Summaries
          </button>
          <button 
            className={`px-4 py-2 rounded ${activeTab === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setActiveTab('all')}
          >
            All Reports
          </button>
          <button
            className="px-4 py-2 rounded bg-green-600 text-white"
            onClick={() => setIsModalOpen(true)}
          >
            New Report
          </button>
        </div>
      </div>
      
      {/* Success Message */}
      {message && showMessage && (
        <div className="mb-4 p-4 bg-green-100 border-l-4 border-green-500 text-green-700 rounded flex justify-between items-start">
          <div>{message}</div>
          <button 
            onClick={() => setShowMessage(false)} 
            className="text-green-700 hover:text-green-900"
          >
            ×
          </button>
        </div>
      )}
      
      {/* Error Message */}
      {errorMessage && (
        <div className="mb-4 p-4 bg-red-100 border-l-4 border-red-500 text-red-700 rounded flex justify-between items-start">
          <div>{errorMessage}</div>
          <button 
            onClick={() => setErrorMessage(null)} 
            className="text-red-700 hover:text-red-900"
          >
            ×
          </button>
        </div>
      )}
      
      {/* Report List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        {isLoading ? (
          <div className="p-6 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading reports...</p>
          </div>
        ) : filteredReports.length === 0 ? (
          <div className="p-6 text-center">
            <p className="text-gray-600">No reports found.</p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="mt-2 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              Generate a new report
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredReports.map((report) => (
                  <tr key={report.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{report.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        {report.type}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-500">{report.description}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{report.generated}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        report.status === 'complete' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {report.status === 'complete' ? 'Completed' : 'Processing'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <Link
                        to={`/reports/${report.id}`}
                        className={`text-blue-600 hover:text-blue-900 mr-3 ${report.status !== 'complete' ? 'opacity-50 cursor-not-allowed' : ''}`}
                      >
                        View
                      </Link>
                      <button
                        className="text-red-600 hover:text-red-900"
                        onClick={() => {
                          // Delete report functionality would go here
                          setReports(reports.filter(r => r.id !== report.id));
                        }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      {/* New Report Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold">Create New Report</h2>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>
              
              <form onSubmit={(e) => {
                e.preventDefault();
                handleSubmitReport();
              }}>
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
                          onClick={() => {
                            if (source.isConnected) {
                              handleSourceToggle(source.id);
                            }
                          }}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              <input
                                type="checkbox"
                                checked={selectedDataSources.includes(source.id)}
                                onChange={() => {}}
                                disabled={!source.isConnected}
                                className="mr-2"
                              />
                              <span className="font-medium">{source.name}</span>
                            </div>
                            {source.status === 'coming_soon' && (
                              <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                                Coming Soon
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-500 mt-1">{source.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* Submit Button */}
                  <div className="mt-6 flex justify-end">
                    <button
                      type="button"
                      onClick={() => setIsModalOpen(false)}
                      className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 mr-3"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="bg-blue-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-blue-700 disabled:bg-blue-300"
                      disabled={isGenerating || !reportTitle || !reportType || selectedDataSources.length === 0}
                    >
                      {isGenerating ? (
                        <div className="flex items-center">
                          <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Generating...
                        </div>
                      ) : (
                        'Generate Report'
                      )}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;
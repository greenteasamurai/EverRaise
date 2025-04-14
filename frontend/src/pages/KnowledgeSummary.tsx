import React, { useState, useEffect } from 'react';

// Sample data for demonstration
const knowledgeSources = [
  {
    id: "gmail",
    name: "Gmail",
    description: "Email messages from Gmail",
    status: "available",
    isConnected: true,
    lastUpdated: "2023-07-15T14:30:00Z"
  },
  {
    id: "slack",
    name: "Slack",
    description: "Messages and channels from Slack",
    status: "coming_soon",
    isConnected: false,
    lastUpdated: null
  },
  {
    id: "github",
    name: "GitHub",
    description: "Pull requests, issues, and commits",
    status: "available",
    isConnected: true,
    lastUpdated: "2023-07-14T10:15:00Z"
  },
  {
    id: "gdrive",
    name: "Google Drive",
    description: "Documents and files from Google Drive",
    status: "available",
    isConnected: false,
    lastUpdated: null
  }
];

const knowledgeClusters = [
  {
    id: "project_statuses",
    name: "Project Statuses",
    description: "Summary of all project statuses and recent updates",
    sources: ["gmail", "github"],
    lastUpdated: "2023-07-15T15:45:00Z"
  },
  {
    id: "team_communications",
    name: "Team Communications",
    description: "Summary of internal team discussions and decisions",
    sources: ["gmail"],
    lastUpdated: "2023-07-15T14:35:00Z"
  },
  {
    id: "external_feedback",
    name: "External Feedback",
    description: "Summary of feedback from customers and partners",
    sources: ["gmail"],
    lastUpdated: "2023-07-15T14:30:00Z"
  }
];

// Sample summary data
const sampleSummary: {
  sources: {
    [key: string]: {
      summary: string;
      lastUpdated: string;
    };
  };
  clusters: {
    [key: string]: {
      summary: string;
      lastUpdated: string;
    };
  };
} = {
  sources: {
    "gmail": {
      summary: "## Email Communications (Last 7 Days)\n\n### Key Themes\n- Product feedback from beta users (mostly positive)\n- Scheduling for upcoming investor meetings\n- Team coordination on release timeline\n\n### Important Threads\n- **Beta Feedback Compilation** - 12 users reported positive experiences with the new UI\n- **Investor Update Preparation** - Need to prepare financial projections by Friday\n- **Release Planning** - Engineering team confirmed on-track for July 30 release\n\n### Action Items\n- Respond to Johnson Capital by EOD with availability\n- Schedule design review for Thursday\n- Confirm marketing materials are ready for release",
      lastUpdated: "2023-07-15T14:30:00Z"
    },
    "github": {
      summary: "## GitHub Activity (Last 7 Days)\n\n### Overview\n- 37 PRs merged\n- 15 issues closed\n- 3 new features completed\n\n### Key Contributions\n- Frontend team completed responsive design implementation\n- Backend team optimized database queries, reducing load time by 40%\n- Security fixes implemented for all identified vulnerabilities\n\n### Open Items\n- 4 critical bugs remaining for current sprint\n- Documentation updates needed for API changes\n- Performance testing on high-volume scenarios",
      lastUpdated: "2023-07-14T10:15:00Z"
    }
  },
  clusters: {
    "project_statuses": {
      summary: "## Project Status Summary\n\n### Product Development\n- Core features 95% complete for July release\n- QA has approved 80% of features\n- Performance metrics exceeding targets\n\n### Marketing & Sales\n- Launch campaign materials approved\n- Sales team trained on new features\n- First demo scheduled with strategic partners\n\n### Operations\n- Infrastructure scaled to handle expected traffic increase\n- Monitoring systems in place\n- Support team staffing increased for launch period",
      lastUpdated: "2023-07-15T15:45:00Z"
    },
    "team_communications": {
      summary: "## Team Communication Summary\n\n### Decision Log\n- Decided to postpone Feature X to next release\n- Approved additional budget for cloud resources\n- Extended beta test period by one week\n\n### Team Morale & Concerns\n- Engineering team working additional hours but spirit remains high\n- Design team expressed concerns about timeline for UI review\n- Customer success team fully prepared for launch\n\n### Coordination Points\n- Daily standups moved to 9:30 AM\n- Release readiness review scheduled for July 25\n- All hands demo planned for July 28",
      lastUpdated: "2023-07-15T14:35:00Z"
    },
    "external_feedback": {
      summary: "## External Feedback Summary\n\n### Customer Feedback\n- Beta users reporting 90% satisfaction with new features\n- Main praise: speed improvements and intuitive design\n- Main concerns: learning curve for power users\n\n### Partner Feedback\n- Integration partners successfully tested API changes\n- Resellers excited about new feature set\n- Strategic partners requesting additional customization options\n\n### Market Perception\n- Industry blog mentions increased 45% this month\n- Competitive analysis shows our solution now leading in 3 categories\n- Social media sentiment trending positive",
      lastUpdated: "2023-07-15T14:30:00Z"
    }
  }
};

const KnowledgeSummary: React.FC = () => {
  const [summaryType, setSummaryType] = useState<'sources' | 'clusters'>('sources');
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // Set default selection when type changes
  useEffect(() => {
    if (summaryType === 'sources' && knowledgeSources.some(s => s.isConnected)) {
      const connectedSource = knowledgeSources.find(s => s.isConnected);
      setSelectedItem(connectedSource?.id || null);
    } else if (summaryType === 'clusters' && knowledgeClusters.length > 0) {
      setSelectedItem(knowledgeClusters[0].id);
    } else {
      setSelectedItem(null);
    }
  }, [summaryType]);
  
  // Load summary when selected item changes
  useEffect(() => {
    if (!selectedItem) {
      setSummary(null);
      setLastUpdated(null);
      return;
    }
    
    // In a real implementation, this would make an API call to get the summary
    // For now, we'll just use the sample data
    const loadSummary = async () => {
      setIsGeneratingSummary(true);
      
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 600));
        
        if (summaryType === 'sources') {
          setSummary(sampleSummary.sources[selectedItem]?.summary || null);
          setLastUpdated(sampleSummary.sources[selectedItem]?.lastUpdated || null);
        } else {
          setSummary(sampleSummary.clusters[selectedItem]?.summary || null);
          setLastUpdated(sampleSummary.clusters[selectedItem]?.lastUpdated || null);
        }
      } catch (error) {
        console.error('Error loading summary:', error);
        setErrorMessage('Failed to load summary data. Please try again.');
      } finally {
        setIsGeneratingSummary(false);
      }
    };
    
    loadSummary();
  }, [selectedItem, summaryType]);
  
  // Handle refreshing the summary
  const handleRefreshSummary = async () => {
    if (!selectedItem) return;
    
    setIsRefreshing(true);
    setErrorMessage(null);
    
    try {
      // In a real implementation, this would make an API call to refresh the summary
      // For now, we'll just simulate a delay
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Update the UI to reflect refreshed data
      // For the demo, we'll just update the timestamp
      const now = new Date().toISOString();
      setLastUpdated(now);
      
      // Show success message
      setErrorMessage("Successfully refreshed summary data.");
    } catch (error) {
      console.error('Error refreshing summary:', error);
      setErrorMessage('Failed to refresh summary. Please try again.');
    } finally {
      setIsRefreshing(false);
    }
  };
  
  // Render the source/cluster selection sidebar
  const renderSelectionSidebar = () => {
    const items = summaryType === 'sources' ? knowledgeSources : knowledgeClusters;
    
    if (summaryType === 'sources') {
      return (
        <div className="w-full lg:w-64 mb-4 lg:mb-0 lg:mr-4">
          <h2 className="text-lg font-semibold mb-2">Knowledge Sources</h2>
          <div className="space-y-2">
            {knowledgeSources.map(source => (
              <div
                key={source.id}
                className={`p-3 border rounded-lg cursor-pointer ${
                  !source.isConnected ? 'opacity-50 cursor-not-allowed' : 
                  selectedItem === source.id ? 'border-blue-500 bg-blue-50' : ''
                }`}
                onClick={() => source.isConnected && setSelectedItem(source.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="font-medium">{source.name}</div>
                  {!source.isConnected && (
                    <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                      Not Connected
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">{source.description}</p>
                {source.lastUpdated && (
                  <div className="text-xs text-gray-500 mt-1">
                    Last updated: {new Date(source.lastUpdated).toLocaleDateString()}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      );
    } else {
      return (
        <div className="w-full lg:w-64 mb-4 lg:mb-0 lg:mr-4">
          <h2 className="text-lg font-semibold mb-2">Knowledge Clusters</h2>
          <div className="space-y-2">
            {knowledgeClusters.map(cluster => (
              <div
                key={cluster.id}
                className={`p-3 border rounded-lg cursor-pointer ${
                  selectedItem === cluster.id ? 'border-blue-500 bg-blue-50' : ''
                }`}
                onClick={() => setSelectedItem(cluster.id)}
              >
                <div className="font-medium">{cluster.name}</div>
                <p className="text-sm text-gray-600 mt-1">{cluster.description}</p>
                {cluster.lastUpdated && (
                  <div className="text-xs text-gray-500 mt-1">
                    Last updated: {new Date(cluster.lastUpdated).toLocaleDateString()}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      );
    }
  };
  
  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Knowledge Summary</h1>
        <div className="flex space-x-4">
          <div className="bg-gray-100 p-1 rounded-lg">
            <button
              className={`px-4 py-2 rounded-md ${
                summaryType === 'sources' ? 'bg-white shadow' : ''
              }`}
              onClick={() => setSummaryType('sources')}
            >
              By Source
            </button>
            <button
              className={`px-4 py-2 rounded-md ${
                summaryType === 'clusters' ? 'bg-white shadow' : ''
              }`}
              onClick={() => setSummaryType('clusters')}
            >
              By Cluster
            </button>
          </div>
          
          <button
            className="px-4 py-2 rounded bg-green-600 text-white flex items-center"
            onClick={handleRefreshSummary}
            disabled={isRefreshing || !selectedItem || isGeneratingSummary}
          >
            {isRefreshing ? (
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
                Refresh
              </>
            )}
          </button>
        </div>
      </div>
      
      {errorMessage && (
        <div className={`mb-4 p-3 border rounded ${
          errorMessage.includes('Failed') ? 'bg-red-100 border-red-400 text-red-700' : 'bg-green-100 border-green-400 text-green-700'
        }`}>
          {errorMessage}
        </div>
      )}
      
      <div className="flex flex-col lg:flex-row">
        {renderSelectionSidebar()}
        
        <div className="flex-1 bg-white rounded-lg shadow p-4">
          {isGeneratingSummary ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <svg className="animate-spin mx-auto h-10 w-10 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p className="mt-3 text-gray-600">Generating summary...</p>
              </div>
            </div>
          ) : selectedItem && summary ? (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">
                  {summaryType === 'sources' 
                    ? knowledgeSources.find(s => s.id === selectedItem)?.name 
                    : knowledgeClusters.find(c => c.id === selectedItem)?.name} Summary
                </h2>
                {lastUpdated && (
                  <div className="text-sm text-gray-500">
                    Last updated: {new Date(lastUpdated).toLocaleString()}
                  </div>
                )}
              </div>
              <div className="prose max-w-none">
                {summary.split('\n').map((line, i) => {
                  if (line.startsWith('## ')) {
                    return <h2 key={i} className="text-xl font-bold mt-4">{line.replace('## ', '')}</h2>;
                  } else if (line.startsWith('### ')) {
                    return <h3 key={i} className="text-lg font-semibold mt-3">{line.replace('### ', '')}</h3>;
                  } else if (line.startsWith('- ')) {
                    return <li key={i} className="ml-4">{line.replace('- ', '')}</li>;
                  } else if (line.startsWith('**') && line.endsWith('**')) {
                    return <p key={i} className="font-bold">{line.replace(/^\*\*|\*\*$/g, '')}</p>;
                  } else if (line === '') {
                    return <br key={i} />;
                  } else {
                    return <p key={i}>{line}</p>;
                  }
                })}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-500">
              {summaryType === 'sources' && !knowledgeSources.some(s => s.isConnected) ? (
                <div className="text-center">
                  <p>No connected data sources found.</p>
                  <p className="mt-2">Please connect a data source in the Integrations tab.</p>
                </div>
              ) : (
                <p>Select a {summaryType === 'sources' ? 'source' : 'cluster'} to view its summary</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeSummary; 
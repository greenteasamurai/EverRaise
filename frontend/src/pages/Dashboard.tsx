import React from 'react'

// Sample data for demonstration
const metrics = [
  { id: 1, name: "Total Donations", value: "$45,231", change: "+20.1%", status: "positive" },
  { id: 2, name: "Active Campaigns", value: "12", change: "+2", status: "positive" },
  { id: 3, name: "Total Donors", value: "2,541", change: "+180", status: "positive" },
  { id: 4, name: "Conversion Rate", value: "3.2%", change: "+0.4%", status: "positive" }
]

const campaigns = [
  { id: 1, name: "Community Garden Project", status: "active", goal: "$15,000", raised: "$12,450", progress: 83 },
  { id: 2, name: "School Library Renovation", status: "active", goal: "$25,000", raised: "$8,760", progress: 35 },
  { id: 3, name: "Animal Shelter Support", status: "pending", goal: "$10,000", raised: "$2,300", progress: 23 },
  { id: 4, name: "Youth Sports Program", status: "active", goal: "$8,500", raised: "$7,650", progress: 90 }
]

const Dashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-medium tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground text-sm mt-1">Overview of your fundraising activities</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button className="inline-flex items-center justify-center text-sm h-9 px-3 py-2 rounded-md border border-border bg-background hover:bg-secondary/40 transition-colors">
            <svg className="mr-2" width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M7.5 12.5V2.5M7.5 2.5L11.5 6.5M7.5 2.5L3.5 6.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Export
          </button>
          
          <button className="inline-flex items-center justify-center h-9 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors">
            <svg className="mr-2" width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M7.5 2.5V12.5M2.5 7.5H12.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            New Campaign
          </button>
        </div>
      </div>
      
      {/* Metrics Grid */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map(metric => (
          <div key={metric.id} className="dashboard-card">
            <div className="flex flex-col">
              <div className="dashboard-label">{metric.name}</div>
              <div className="dashboard-stat mt-1">{metric.value}</div>
              <div className={`text-xs mt-1 ${metric.status === 'positive' ? 'text-emerald-500' : 'text-red-500'}`}>
                {metric.change}
                {metric.status === 'positive' ? (
                  <svg className="inline-block ml-1 mb-0.5" width="10" height="10" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M5 2.5V7.5M5 2.5L2.5 5M5 2.5L7.5 5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                ) : (
                  <svg className="inline-block ml-1 mb-0.5" width="10" height="10" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M5 7.5V2.5M5 7.5L7.5 5M5 7.5L2.5 5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Campaigns Table */}
      <div className="dashboard-card overflow-hidden">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-medium">Active Campaigns</h2>
          <button className="text-xs text-primary hover:underline">View All</button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full divide-y divide-border/60">
            <thead>
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Name</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Goal</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Raised</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Progress</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {campaigns.map(campaign => (
                <tr key={campaign.id} className="hover:bg-secondary/40 transition-colors">
                  <td className="px-3 py-3 text-sm font-medium">{campaign.name}</td>
                  <td className="px-3 py-3 text-sm">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      campaign.status === 'active' ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'
                    }`}>
                      {campaign.status === 'active' ? (
                        <>
                          <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                          Active
                        </>
                      ) : (
                        <>
                          <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-amber-500"></span>
                          Pending
                        </>
                      )}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-sm">{campaign.goal}</td>
                  <td className="px-3 py-3 text-sm">{campaign.raised}</td>
                  <td className="px-3 py-3 text-sm">
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 h-1.5 bg-secondary rounded-full">
                        <div 
                          className="h-full bg-primary rounded-full" 
                          style={{ width: `${campaign.progress}%` }} 
                        />
                      </div>
                      <span className="text-xs font-medium">{campaign.progress}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Dashboard 
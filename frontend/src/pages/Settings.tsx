import React, { useState } from 'react'

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState('account')

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-medium tracking-tight">Settings</h1>
        <p className="text-muted-foreground text-sm mt-1">Manage your account and preferences</p>
      </div>
      
      {/* Settings Tabs */}
      <div className="flex space-x-1 border-b">
        {['account', 'notifications', 'security', 'integrations'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-primary text-foreground font-medium'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>
      
      {/* Account Settings */}
      {activeTab === 'account' && (
        <div className="dashboard-card">
          <h2 className="text-lg font-medium mb-4">Account Information</h2>
          
          <div className="space-y-6">
            <div className="space-y-1">
              <label className="block text-sm font-medium" htmlFor="name">
                Full Name
              </label>
              <input
                id="name"
                type="text"
                defaultValue="Jane Smith"
                className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
              />
            </div>
            
            <div className="space-y-1">
              <label className="block text-sm font-medium" htmlFor="email">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                defaultValue="jane.smith@example.com"
                className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
              />
            </div>
            
            <div className="space-y-1">
              <label className="block text-sm font-medium" htmlFor="organization">
                Organization
              </label>
              <input
                id="organization"
                type="text"
                defaultValue="Acme Nonprofit"
                className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
              />
            </div>
            
            <div className="pt-5">
              <div className="flex justify-end">
                <button
                  type="button"
                  className="mr-3 rounded-md border border-border bg-background px-3 py-2 text-sm hover:bg-secondary/40 focus:outline-none focus:ring-2 focus:ring-primary/30"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="inline-flex justify-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/30"
                >
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Notifications Settings */}
      {activeTab === 'notifications' && (
        <div className="dashboard-card">
          <h2 className="text-lg font-medium mb-4">Notification Preferences</h2>
          
          <div className="space-y-4">
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  id="email-notifications"
                  name="email-notifications"
                  type="checkbox"
                  defaultChecked
                  className="h-4 w-4 rounded border-border text-primary focus:ring-primary/30"
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor="email-notifications" className="font-medium">
                  Email Notifications
                </label>
                <p className="text-muted-foreground">Receive campaign updates and fundraising milestones via email</p>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  id="donation-alerts"
                  name="donation-alerts"
                  type="checkbox"
                  defaultChecked
                  className="h-4 w-4 rounded border-border text-primary focus:ring-primary/30"
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor="donation-alerts" className="font-medium">
                  Donation Alerts
                </label>
                <p className="text-muted-foreground">Get notified when your campaigns receive new donations</p>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  id="report-notifications"
                  name="report-notifications"
                  type="checkbox"
                  className="h-4 w-4 rounded border-border text-primary focus:ring-primary/30"
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor="report-notifications" className="font-medium">
                  Report Generation Notifications
                </label>
                <p className="text-muted-foreground">Receive notifications when reports are generated or ready to view</p>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  id="newsletter"
                  name="newsletter"
                  type="checkbox"
                  defaultChecked
                  className="h-4 w-4 rounded border-border text-primary focus:ring-primary/30"
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor="newsletter" className="font-medium">
                  Monthly Newsletter
                </label>
                <p className="text-muted-foreground">Stay updated with fundraising tips and product updates</p>
              </div>
            </div>
            
            <div className="pt-5">
              <div className="flex justify-end">
                <button
                  type="submit"
                  className="inline-flex justify-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/30"
                >
                  Save Preferences
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Security Settings */}
      {activeTab === 'security' && (
        <div className="dashboard-card">
          <h2 className="text-lg font-medium mb-4">Security Settings</h2>
          
          <div className="space-y-6">
            <div className="space-y-1">
              <label className="block text-sm font-medium" htmlFor="current-password">
                Current Password
              </label>
              <input
                id="current-password"
                type="password"
                className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
              />
            </div>
            
            <div className="space-y-1">
              <label className="block text-sm font-medium" htmlFor="new-password">
                New Password
              </label>
              <input
                id="new-password"
                type="password"
                className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
              />
            </div>
            
            <div className="space-y-1">
              <label className="block text-sm font-medium" htmlFor="confirm-password">
                Confirm Password
              </label>
              <input
                id="confirm-password"
                type="password"
                className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
              />
            </div>
            
            <div className="pt-5">
              <div className="flex justify-end">
                <button
                  type="submit"
                  className="inline-flex justify-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/30"
                >
                  Update Password
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Integrations Settings */}
      {activeTab === 'integrations' && (
        <div className="dashboard-card">
          <h2 className="text-lg font-medium mb-4">Connected Services</h2>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center p-4 border rounded-md">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-[#4285F4] rounded-full flex items-center justify-center text-white">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path>
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium">Facebook</h3>
                  <p className="text-xs text-muted-foreground">Connected</p>
                </div>
              </div>
              <button className="text-sm text-primary hover:underline">Disconnect</button>
            </div>
            
            <div className="flex justify-between items-center p-4 border rounded-md">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-[#1DA1F2] rounded-full flex items-center justify-center text-white">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"></path>
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium">Twitter</h3>
                  <p className="text-xs text-muted-foreground">Not connected</p>
                </div>
              </div>
              <button className="text-sm text-primary hover:underline">Connect</button>
            </div>
            
            <div className="flex justify-between items-center p-4 border rounded-md">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-[#DB4437] rounded-full flex items-center justify-center text-white">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z"></path>
                    <polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02"></polygon>
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium">YouTube</h3>
                  <p className="text-xs text-muted-foreground">Connected</p>
                </div>
              </div>
              <button className="text-sm text-primary hover:underline">Disconnect</button>
            </div>
            
            <div className="flex justify-between items-center p-4 border rounded-md">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-gray-500 rounded-full flex items-center justify-center text-white">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                    <rect x="2" y="9" width="4" height="12"></rect>
                    <circle cx="4" cy="4" r="2"></circle>
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium">LinkedIn</h3>
                  <p className="text-xs text-muted-foreground">Not connected</p>
                </div>
              </div>
              <button className="text-sm text-primary hover:underline">Connect</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Settings 
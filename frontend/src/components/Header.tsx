import React from 'react'
import { useNavigate } from 'react-router-dom'
import BackendStatusIndicator from './BackendStatusIndicator'
import { removeToken } from '../utils/auth'

const Header: React.FC = () => {
  const navigate = useNavigate();
  
  // Function to handle logout
  const handleLogout = () => {
    removeToken(); // Remove the auth token
    navigate('/login'); // Redirect to login page
  };
  
  return (
    <header className="border-b border-border/20 h-16 px-6 md:px-8 flex items-center justify-between bg-background backdrop-blur-sm bg-opacity-80 z-10">
      <div className="flex items-center">
        <span className="text-base font-semibold tracking-tight">EverRaise</span>
      </div>
      
      <div className="flex items-center space-x-6">
        <BackendStatusIndicator />
        
        <button className="text-muted-foreground hover:text-foreground transition-colors" aria-label="Search">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M15.7955 15.8111L21 21M18 10.5C18 14.6421 14.6421 18 10.5 18C6.35786 18 3 14.6421 3 10.5C3 6.35786 6.35786 3 10.5 3C14.6421 3 18 6.35786 18 10.5Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
        
        <button className="text-muted-foreground hover:text-foreground transition-colors relative" aria-label="Notifications">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9.10745 2.67414C9.98414 2.24182 10.9649 2 12 2C15.866 2 19 5.13401 19 9C19 10.0353 19.7159 11.1007 20.4331 11.9497C21.0986 12.7252 21.7154 13.5503 21.9248 14.2516C22.2352 15.3305 21.6403 16.3326 20.5998 16.6634C19.8438 16.8862 18.7963 17 17.5 17M6.5 17C5.20371 17 4.15618 16.8862 3.40018 16.6634C2.35965 16.3326 1.76481 15.3305 2.07515 14.2516C2.28459 13.5503 2.90136 12.7252 3.56685 11.9497C4.28407 11.1007 5 10.0353 5 9C5 7.93512 5.24183 6.9544 5.67414 6.07769M12 17V20M8.5 22H15.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span className="absolute -top-1 -right-1 flex h-4 w-4">
            <span className="relative inline-flex rounded-full h-2 w-2 bg-destructive"></span>
          </span>
        </button>
        
        {/* Logout button */}
        <button 
          onClick={handleLogout}
          className="text-sm font-medium text-red-500 hover:text-red-700 transition-colors"
        >
          Logout
        </button>
        
        <div className="flex items-center">
          <div className="w-8 h-8 rounded-full flex items-center justify-center ring-1 ring-border/40 bg-background overflow-hidden">
            <span className="text-xs font-medium">EV</span>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header 
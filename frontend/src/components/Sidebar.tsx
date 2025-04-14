import React from 'react'
import { Link, useLocation } from 'react-router-dom'

const navItems = [
  {
    name: 'Dashboard',
    href: '/',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M9 4H5C4.44772 4 4 4.44772 4 5V9C4 9.55228 4.44772 10 5 10H9C9.55228 10 10 9.55228 10 9V5C10 4.44772 9.55228 4 9 4Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M19 4H15C14.4477 4 14 4.44772 14 5V9C14 9.55228 14.4477 10 15 10H19C19.5523 10 20 9.55228 20 9V5C20 4.44772 19.5523 4 19 4Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M9 14H5C4.44772 14 4 14.4477 4 15V19C4 19.5523 4.44772 20 5 20H9C9.55228 20 10 19.5523 10 19V15C10 14.4477 9.55228 14 9 14Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M19 14H15C14.4477 14 14 14.4477 14 15V19C14 19.5523 14.4477 20 15 20H19C19.5523 20 20 19.5523 20 19V15C20 14.4477 19.5523 14 19 14Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    )
  },
  {
    name: 'Integrations',
    href: '/integrations',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M9.1709 4.1709C9.58254 2.66914 11.2691 1.82722 12.7709 2.23886C14.2726 2.65049 15.1145 4.33701 14.7029 5.83877C14.2913 7.34053 12.6047 8.18245 11.103 7.77081C9.6012 7.35918 8.75928 5.67266 9.1709 4.1709Z" stroke="currentColor" strokeWidth="1.5"/>
        <path d="M9.1709 19.8291C9.58254 18.3274 11.2691 17.4855 12.7709 17.8971C14.2726 18.3087 15.1145 19.9953 14.7029 21.497C14.2913 22.9988 12.6047 23.8407 11.103 23.4291C9.6012 23.0174 8.75928 21.3309 9.1709 19.8291Z" stroke="currentColor" strokeWidth="1.5"/>
        <path d="M19.8291 9.1709C18.3274 9.58254 17.4855 11.2691 17.8971 12.7709C18.3087 14.2726 19.9953 15.1145 21.497 14.7029C22.9988 14.2913 23.8407 12.6047 23.4291 11.103C23.0174 9.6012 21.3309 8.75928 19.8291 9.1709Z" stroke="currentColor" strokeWidth="1.5"/>
        <path d="M4.1709 9.1709C2.66914 9.58254 1.82722 11.2691 2.23886 12.7709C2.65049 14.2726 4.33701 15.1145 5.83877 14.7029C7.34053 14.2913 8.18245 12.6047 7.77081 11.103C7.35918 9.6012 5.67266 8.75928 4.1709 9.1709Z" stroke="currentColor" strokeWidth="1.5"/>
        <path d="M9.17096 4.17097L9.17096 4.17097C9.58259 2.66921 11.2691 1.82729 12.7709 2.23893" stroke="currentColor" strokeWidth="1.5"/>
        <path d="M4.17096 9.17096C2.66921 9.58259 1.82729 11.2691 2.23893 12.7709" stroke="currentColor" strokeWidth="1.5"/>
        <path d="M14.7029 21.497L14.7029 21.497C14.2913 22.9988 12.6048 23.8407 11.103 23.4291" stroke="currentColor" strokeWidth="1.5"/>
        <path d="M19.8291 9.17097C21.3308 8.75934 23.0174 9.60126 23.429 11.103" stroke="currentColor" strokeWidth="1.5"/>
      </svg>
    )
  },
  {
    name: 'Report Generation',
    href: '/report-generation',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M14 3V7C14 7.26522 14.1054 7.51957 14.2929 7.70711C14.4804 7.89464 14.7348 8 15 8H19" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M5 8V5C5 4.46957 5.21071 3.96086 5.58579 3.58579C5.96086 3.21071 6.46957 3 7 3H14L19 8V19C19 19.5304 18.7893 20.0391 18.4142 20.4142C18.0391 20.7893 17.5304 21 17 21H7C6.46957 21 5.96086 20.7893 5.58579 20.4142C5.21071 20.0391 5 19.5304 5 19V16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M5 16H3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M3 16V8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M3 8H5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M9 12H12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M9 16H15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    )
  },
  {
    name: 'Knowledge Summary',
    href: '/knowledge-summary',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M8 16H16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M8 12H16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M8 8H12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M3 20.29V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7C5.9 17 4.1 17.3 3 20.29Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    )
  },
  {
    name: 'Reports',
    href: '/reports',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M9 17H15M9 13H15M9 9H10M17 21H7C5.89543 21 5 20.1046 5 19V5C5 3.89543 5.89543 3 7 3H12.5858C12.851 3 13.1054 3.10536 13.2929 3.29289L18.7071 8.70711C18.8946 8.89464 19 9.149 19 9.41421V19C19 20.1046 18.1046 21 17 21Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    )
  },
  {
    name: 'System Status',
    href: '/system-status',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 6H21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M5 6V4C5 3.73478 5.10536 3.48043 5.29289 3.29289C5.48043 3.10536 5.73478 3 6 3H18C18.2652 3 18.5196 3.10536 18.7071 3.29289C18.8946 3.48043 19 3.73478 19 4V6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M8 14V16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M12 12V16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M16 10V16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M9 21H15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M12 16V21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M4 6V14C4 14.2652 4.10536 14.5196 4.29289 14.7071C4.48043 14.8946 4.73478 15 5 15H19C19.2652 15 19.5196 14.8946 19.7071 14.7071C19.8946 14.5196 20 14.2652 20 14V6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    )
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M19.4 15C19.1277 15.6171 19.2583 16.3378 19.73 16.82L19.79 16.88C20.1656 17.2551 20.3766 17.7642 20.3766 18.295C20.3766 18.8258 20.1656 19.3349 19.79 19.71C19.4149 20.0856 18.9058 20.2966 18.375 20.2966C17.8442 20.2966 17.3351 20.0856 16.96 19.71L16.9 19.65C16.4178 19.1783 15.6971 19.0477 15.08 19.32C14.4755 19.5791 14.0826 20.1789 14.08 20.83V21C14.08 22.1046 13.1846 23 12.08 23C10.9754 23 10.08 22.1046 10.08 21V20.91C10.0642 20.2516 9.64573 19.6591 9.00003 19.42C8.38297 19.1477 7.66225 19.2783 7.18003 19.75L7.12003 19.81C6.7449 20.1856 6.23578 20.3966 5.70503 20.3966C5.17427 20.3966 4.66516 20.1856 4.29003 19.81C3.91445 19.4349 3.70343 18.9258 3.70343 18.395C3.70343 17.8642 3.91445 17.3551 4.29003 16.98L4.35003 16.92C4.82168 16.4378 4.95235 15.7171 4.68003 15.1C4.42093 14.4955 3.82109 14.1026 3.17003 14.1H3.00003C1.89546 14.1 1.00003 13.2046 1.00003 12.1C1.00003 10.9954 1.89546 10.1 3.00003 10.1H3.09003C3.74841 10.0842 4.3409 9.66572 4.58003 9.02002C4.85235 8.40296 4.72168 7.68224 4.25003 7.20002L4.19003 7.14002C3.81445 6.76489 3.60343 6.25578 3.60343 5.72502C3.60343 5.19427 3.81445 4.68516 4.19003 4.31002C4.56516 3.93445 5.07427 3.72342 5.60503 3.72342C6.13578 3.72342 6.6449 3.93445 7.02003 4.31002L7.08003 4.37003C7.56225 4.84168 8.28297 4.97235 8.90003 4.70002H9.00003C9.60446 4.43923 10.0273 3.83939 10.03 3.19003V3.00002C10.03 1.89545 10.9254 1.00002 12.03 1.00002C13.1346 1.00002 14.03 1.89545 14.03 3.00002V3.09002C14.0326 3.73938 14.4556 4.33922 15.06 4.60002H15.16C15.777 4.87235 16.4978 4.74168 16.98 4.27002L17.04 4.21002C17.4151 3.83445 17.9242 3.62342 18.455 3.62342C18.9858 3.62342 19.4949 3.83445 19.87 4.21002C20.2456 4.58516 20.4566 5.09427 20.4566 5.62502C20.4566 6.15578 20.2456 6.66489 19.87 7.04002L19.81 7.10002C19.3384 7.58224 19.2077 8.30292 19.48 8.92002V9.02002C19.7408 9.62446 20.3407 10.0473 20.99 10.05H21C22.1046 10.05 23 10.9454 23 12.05C23 13.1546 22.1046 14.05 21 14.05H20.91C20.2607 14.0527 19.6608 14.4755 19.4 15.08V15Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    )
  }
];

const Sidebar: React.FC = () => {
  const location = useLocation();
  
  return (
    <aside className="h-screen bg-card border-r border-border/50 w-20 md:w-64 flex flex-col">
      {/* Logo */}
      <div className="h-16 border-b border-border/50 flex items-center justify-center md:justify-start px-4">
        <div className="w-10 h-10 rounded-xl bg-primary/20 text-primary flex items-center justify-center">
          <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
            <span className="text-xs text-white font-semibold">+</span>
          </div>
        </div>
        <span className="hidden md:block ml-3 font-medium text-sm">EverRaise</span>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 py-6">
        <ul className="space-y-1 px-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.href || 
              (item.href !== '/' && location.pathname.startsWith(item.href));
            
            return (
              <li key={item.name}>
                <Link
                  to={item.href}
                  className={`flex items-center px-3 py-2.5 rounded-md text-sm group transition-colors ${
                    isActive 
                      ? 'bg-primary/10 text-primary font-medium' 
                      : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
                  }`}
                >
                  <span className={`${isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'}`}>
                    {item.icon}
                  </span>
                  <span className="ml-3 hidden md:block">{item.name}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      
      {/* User Profile */}
      <div className="h-16 border-t border-border/50 flex items-center px-4">
        <div className="w-9 h-9 rounded-full bg-secondary flex items-center justify-center">
          <span className="text-sm font-medium">JS</span>
        </div>
        <div className="ml-3 hidden md:block">
          <div className="text-sm font-medium">John Smith</div>
          <div className="text-xs text-muted-foreground">john@example.com</div>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar 
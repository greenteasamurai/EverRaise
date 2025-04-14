import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import App from './App'
import './styles/globals.css'

// Make sure Tailwind is properly initialized
import 'tailwindcss/tailwind.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

// Simple fallback component to test if basic rendering works
const FallbackComponent = () => {
  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'Arial, sans-serif',
      maxWidth: '800px',
      margin: '40px auto',
      textAlign: 'center',
      border: '1px solid #ccc',
      borderRadius: '8px'
    }}>
      <h1 style={{ color: '#333' }}>EverRaise Application</h1>
      <p style={{ marginTop: '20px' }}>
        If you're seeing this message, React is rendering correctly but there might be an issue with the main application.
      </p>
      <div style={{ marginTop: '20px', background: '#f7f7f7', padding: '15px', borderRadius: '4px', textAlign: 'left' }}>
        <p>Try checking the console (F12) for error messages.</p>
      </div>
    </div>
  );
};

try {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    // Temporarily disable StrictMode to see if it resolves rendering issues
    // <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    // </React.StrictMode>
  );
} catch (error) {
  console.error("Error rendering app:", error);
  
  // Render fallback component if main app fails
  ReactDOM.createRoot(document.getElementById('root')!).render(<FallbackComponent />);
} 
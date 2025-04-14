import React, { useEffect } from 'react';
import { useNavigate, Outlet } from 'react-router-dom';
import { isAuthenticated } from '../utils/auth';

/**
 * ProtectedRoute component
 * Wraps routes that should only be accessible to authenticated users
 * Redirects to login if not authenticated
 */
const ProtectedRoute = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is authenticated
    if (!isAuthenticated()) {
      // Redirect to login page with return_to parameter
      const currentPath = window.location.pathname;
      navigate(`/login?return_to=${encodeURIComponent(currentPath)}`);
    }
  }, [navigate]);

  // Render the child routes if authenticated
  return isAuthenticated() ? <Outlet /> : null;
};

export default ProtectedRoute; 
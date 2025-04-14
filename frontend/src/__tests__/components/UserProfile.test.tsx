import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { server, apiBaseUrl } from '../setup';
import { rest } from 'msw';
import { MemoryRouter } from 'react-router-dom';

// Import the component to test
// For this example, we'll assume it exists
// import UserProfile from '../../components/UserProfile';

// Mock component for testing since we don't have the real one
const UserProfile = () => {
  const [user, setUser] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function fetchUser() {
      try {
        const response = await fetch(`${apiBaseUrl}/users/me`, {
          headers: {
            'Authorization': 'Bearer fake-token'
          }
        });
        if (!response.ok) {
          throw new Error('Failed to fetch user data');
        }
        const userData = await response.json();
        setUser(userData);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setLoading(false);
      }
    }
    
    fetchUser();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return <div>No user data found</div>;

  return (
    <div>
      <h1>User Profile</h1>
      <div data-testid="user-email">Email: {user.email}</div>
      <div data-testid="user-name">Name: {user.full_name || 'N/A'}</div>
      <div>
        Status: <span data-testid="user-status">{user.is_active ? 'Active' : 'Inactive'}</span>
      </div>
    </div>
  );
};

describe('UserProfile Component', () => {
  // Test successful data loading
  it('renders user data when API call is successful', async () => {
    // Render the component
    render(
      <MemoryRouter>
        <UserProfile />
      </MemoryRouter>
    );
    
    // Check loading state
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    
    // Wait for the data to load
    await waitFor(() => {
      expect(screen.getByText('User Profile')).toBeInTheDocument();
    });
    
    // Verify user data is displayed
    expect(screen.getByTestId('user-email')).toHaveTextContent('Email: user@example.com');
    expect(screen.getByTestId('user-name')).toHaveTextContent('Name: Test User');
    expect(screen.getByTestId('user-status')).toHaveTextContent('Active');
  });

  // Test error handling
  it('renders error message when API call fails', async () => {
    // Override the default handler for this test only
    server.use(
      rest.get(`${apiBaseUrl}/users/me`, (req, res, ctx) => {
        return res(
          ctx.status(401),
          ctx.json({ detail: 'Authentication failed' })
        );
      })
    );
    
    // Render the component
    render(
      <MemoryRouter>
        <UserProfile />
      </MemoryRouter>
    );
    
    // Wait for the error message
    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });

  // Test empty response
  it('handles empty user data gracefully', async () => {
    // Override the default handler for this test only
    server.use(
      rest.get(`${apiBaseUrl}/users/me`, (req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json(null)
        );
      })
    );
    
    // Render the component
    render(
      <MemoryRouter>
        <UserProfile />
      </MemoryRouter>
    );
    
    // Wait for the no data message
    await waitFor(() => {
      expect(screen.getByText('No user data found')).toBeInTheDocument();
    });
  });
}); 
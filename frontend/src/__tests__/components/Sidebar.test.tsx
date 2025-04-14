/// <reference types="vitest/globals" />
/// <reference types="@testing-library/jest-dom" />

import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { expect, describe, it, vi } from 'vitest';
import Sidebar from '../../components/Sidebar';

// Mock the useLocation hook
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useLocation: vi.fn()
  };
});

describe('Sidebar Component', () => {
  beforeEach(() => {
    // Reset mocks
    vi.mocked(useLocation).mockReset();
  });

  it('renders without crashing', () => {
    vi.mocked(useLocation).mockReturnValue({ pathname: '/' } as any);
    
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );
    
    // Verify that the app name is shown
    expect(screen.getByText('EverRaise')).toBeInTheDocument();
  });

  it('shows all navigation items', () => {
    vi.mocked(useLocation).mockReturnValue({ pathname: '/' } as any);
    
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );
    
    // Check that all main navigation items exist
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Reports')).toBeInTheDocument();
    expect(screen.getByText('Integrations')).toBeInTheDocument();
    expect(screen.getByText('Report Generation')).toBeInTheDocument();
    expect(screen.getByText('Knowledge Summary')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('highlights the active route', () => {
    // Mock the location to be on the Reports page
    vi.mocked(useLocation).mockReturnValue({ pathname: '/reports' } as any);
    
    const { container } = render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );
    
    // Find the Reports nav item and check its styling
    const reportsLink = screen.getByText('Reports').closest('a');
    expect(reportsLink).toHaveClass('bg-primary/10');
    expect(reportsLink).toHaveClass('text-primary');
  });

  it('shows user profile section', () => {
    vi.mocked(useLocation).mockReturnValue({ pathname: '/' } as any);
    
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );
    
    // Check that user profile info is displayed
    expect(screen.getByText('John Smith')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });
}); 
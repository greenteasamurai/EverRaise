/// <reference types="vitest/globals" />
/// <reference types="@testing-library/jest-dom" />

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, describe, it, vi, beforeEach } from 'vitest';
import Reports from '../../pages/Reports';

// Mock the API utilities
jest.mock('../../utils/api', () => ({
  getApiUrl: jest.fn((endpoint) => `http://localhost:8000${endpoint}`),
}));

// Mock fetch API
global.fetch = vi.fn();

// Mock window.localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  clear: vi.fn()
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('Reports Page', () => {
  beforeEach(() => {
    // Reset mocks
    vi.resetAllMocks();
    
    // Mock successful API response
    global.fetch = vi.fn().mockImplementation((url) => {
      if (url.includes('/api/v1/reports/list')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            {
              id: '1',
              title: 'Q2 Fundraising Overview',
              report_type: 'investor_update',
              summary: 'Summary of fundraising activities',
              created_at: '2023-06-30T10:00:00Z',
              status: 'complete',
              data_sources: ['gmail']
            },
            {
              id: '2',
              title: 'Donor Retention Analysis',
              report_type: 'knowledge_summary',
              summary: 'Analysis of donor retention rates',
              created_at: '2023-05-15T14:30:00Z',
              status: 'complete',
              data_sources: ['gmail']
            }
          ])
        });
      } else if (url.includes('/api/v1/reports/status/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            status: 'complete',
            result: {
              content: {
                executive_summary: '# Executive Summary\n\nThis is a test report.',
                key_metrics: '# Key Metrics\n\n- Metric 1: 42%\n- Metric 2: $1.2M'
              }
            }
          })
        });
      }
      
      return Promise.resolve({ ok: false });
    });
    
    // Setup localStorage mock
    localStorageMock.getItem.mockReturnValue('mock-token');
  });
  
  it('renders the Reports page', async () => {
    render(
      <MemoryRouter>
        <Reports />
      </MemoryRouter>
    );
    
    // Check page title is rendered
    expect(screen.getByText('Reports')).toBeInTheDocument();
    
    // Check tab buttons exist
    expect(screen.getByText('Recent')).toBeInTheDocument();
    expect(screen.getByText('All')).toBeInTheDocument();
    
    // Check Combine Reports button exists
    expect(screen.getByText('Combine Reports')).toBeInTheDocument();
    
    // Wait for reports to be loaded
    await waitFor(() => {
      expect(screen.getByText('Q2 Fundraising Overview')).toBeInTheDocument();
    });
    
    // Verify API was called correctly
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringMatching('/api/v1/reports/list'),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer mock-token'
        })
      })
    );
  });
  
  it('allows selecting and viewing a report', async () => {
    render(
      <MemoryRouter>
        <Reports />
      </MemoryRouter>
    );
    
    // Wait for reports to be loaded
    await waitFor(() => {
      expect(screen.getByText('Q2 Fundraising Overview')).toBeInTheDocument();
    });
    
    // Click the View button on the first report
    const viewButtons = screen.getAllByText('View');
    fireEvent.click(viewButtons[0]);
    
    // Check that report modal is displayed
    await waitFor(() => {
      expect(screen.getByText('Executive Summary')).toBeInTheDocument();
      expect(screen.getByText('This is a test report.')).toBeInTheDocument();
    });
    
    // Check that API was called to get report details
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/reports/status/'),
      expect.any(Object)
    );
  });
  
  it('allows selecting reports for combining', async () => {
    render(
      <MemoryRouter>
        <Reports />
      </MemoryRouter>
    );
    
    // Wait for reports to be loaded
    await waitFor(() => {
      expect(screen.getByText('Q2 Fundraising Overview')).toBeInTheDocument();
    });
    
    // Select reports by clicking checkboxes
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[1]);
    
    // Click the Combine Reports button
    fireEvent.click(screen.getByText('Combine Reports'));
    
    // Check that combine modal is displayed
    await waitFor(() => {
      expect(screen.getByText('Combined Report Title')).toBeInTheDocument();
      expect(screen.getByText('Selected Reports')).toBeInTheDocument();
    });
  });
  
  it('handles API errors gracefully', async () => {
    // Override the mock to simulate an error
    global.fetch = vi.fn().mockImplementation(() => {
      return Promise.resolve({
        ok: false,
        text: () => Promise.resolve('Server error')
      });
    });
    
    render(
      <MemoryRouter>
        <Reports />
      </MemoryRouter>
    );
    
    // Check page renders despite API error
    expect(screen.getByText('Reports')).toBeInTheDocument();
    
    // Verify API was called
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });
    
    // The component should use sample data if API fails
    expect(screen.getByText('No reports found.')).toBeInTheDocument();
  });
}); 
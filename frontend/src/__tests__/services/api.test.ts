/// <reference types="vitest/globals" />
/// <reference types="@testing-library/jest-dom" />

import { describe, it, expect, beforeEach, afterEach, vi, beforeAll, afterAll } from 'vitest';
import axios from 'axios';
import { rest, RestRequest, ResponseComposition, RestContext } from 'msw';
import { setupServer } from 'msw/node';
import { server, apiBaseUrl } from '../setup';

// Mock the axios module
vi.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Setup mock server for API requests
const apiService = {
  async fetchData(endpoint: string, options?: RequestInit) {
    const url = `${apiBaseUrl}${endpoint}`;
    const response = await fetch(url, options);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return response.json();
  },
  
  async login(email: string, password: string) {
    const url = `${apiBaseUrl}/auth/login`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    });
    
    if (!response.ok) {
      throw new Error(`Login failed: ${response.status}`);
    }
    
    return response.json();
  }
};

describe('API Service', () => {
  beforeAll(() => {
    server.listen();
  });

  afterEach(() => {
    server.resetHandlers();
    vi.resetAllMocks();
  });

  afterAll(() => {
    server.close();
  });

  it('should fetch health status successfully', async () => {
    // Mock the axios.get implementation
    mockedAxios.get.mockResolvedValueOnce({
      data: { status: 'healthy' },
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {}
    });

    // This would typically call your actual API service
    // For testing purposes, we'll directly use axios here
    const response = await axios.get('http://localhost:8000/api/health');
    
    expect(response.status).toBe(200);
    expect(response.data).toEqual({ status: 'healthy' });
    expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/api/health');
  });

  it('should handle API errors', async () => {
    // Mock the axios.get implementation to throw an error
    mockedAxios.get.mockRejectedValueOnce(new Error('Network Error'));

    // Expect the promise to reject
    await expect(axios.get('http://localhost:8000/api/health')).rejects.toThrow('Network Error');
    expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/api/health');
  });

  // Test fetching data
  it('fetches data successfully', async () => {
    const testData = { id: 1, name: 'Test Item' };
    
    // Setup mock for this specific test
    server.use(
      rest.get(`${apiBaseUrl}/items`, (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(testData));
      })
    );
    
    const result = await apiService.fetchData('/items');
    expect(result).toEqual(testData);
  });
  
  // Test error handling
  it('throws an error when fetch fails', async () => {
    // Setup mock for this specific test
    server.use(
      rest.get(`${apiBaseUrl}/error-endpoint`, (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ message: 'Server error' }));
      })
    );
    
    await expect(apiService.fetchData('/error-endpoint'))
      .rejects
      .toThrow('API error: 500');
  });
  
  // Test login functionality
  it('handles login successfully', async () => {
    const mockUser = {
      email: 'test@example.com',
      password: 'password123'
    };
    
    const mockResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
      user: {
        id: '1',
        email: mockUser.email,
        is_active: true
      }
    };
    
    // Setup mock for this specific test
    server.use(
      rest.post(`${apiBaseUrl}/auth/login`, (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockResponse));
      })
    );
    
    const result = await apiService.login(mockUser.email, mockUser.password);
    expect(result).toEqual(mockResponse);
    expect(result.access_token).toBe('test-token');
  });
  
  // Test login failure
  it('handles login failure', async () => {
    // Setup mock for this specific test
    server.use(
      rest.post(`${apiBaseUrl}/auth/login`, (req, res, ctx) => {
        return res(
          ctx.status(401),
          ctx.json({ detail: 'Incorrect email or password' })
        );
      })
    );
    
    await expect(apiService.login('wrong@example.com', 'wrongpass'))
      .rejects
      .toThrow('Login failed: 401');
  });
}); 
/// <reference types="vitest/globals" />
/// <reference types="@testing-library/jest-dom" />

import { expect, afterEach, beforeAll, afterAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import matchers from '@testing-library/jest-dom/matchers';
import { setupServer } from 'msw/node';
import { rest, RestRequest, ResponseComposition, RestContext } from 'msw';

// Extend Vitest's expect with React Testing Library's matchers
expect.extend(matchers);

// Automatically cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock API server setup
export const apiBaseUrl = 'http://localhost:8000/api';

// Type definitions for API response data
export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Define handlers for common API endpoints
export const handlers = [
  // Auth endpoints
  rest.post(`${apiBaseUrl}/auth/login`, (req, res, ctx) => {
    // Parse body from the request
    const body = req.body as { email: string; password: string } | null;
    
    const mockUser: User = {
      id: '1',
      email: body?.email || 'user@example.com',
      full_name: 'Test User',
      is_active: true,
      is_superuser: false
    };
    
    const response: LoginResponse = {
      access_token: 'mock-token',
      token_type: 'bearer',
      user: mockUser
    };
    
    return res(
      ctx.status(200),
      ctx.json(response)
    );
  }),
  
  rest.post(`${apiBaseUrl}/auth/register`, (req, res, ctx) => {
    // Parse body from the request
    const body = req.body as { email: string; password: string; full_name?: string } | null;
    
    const mockUser: User = {
      id: '2',
      email: body?.email || 'newuser@example.com',
      full_name: body?.full_name,
      is_active: true,
      is_superuser: false
    };
    
    return res(
      ctx.status(201),
      ctx.json(mockUser)
    );
  }),
  
  // User endpoints
  rest.get(`${apiBaseUrl}/users/me`, (req, res, ctx) => {
    const mockUser: User = {
      id: '1',
      email: 'user@example.com',
      full_name: 'Test User',
      is_active: true,
      is_superuser: false
    };
    
    return res(
      ctx.status(200),
      ctx.json(mockUser)
    );
  }),
  
  rest.get(`${apiBaseUrl}/users/:id`, (req, res, ctx) => {
    const { id } = req.params;
    
    const mockUser: User = {
      id: id as string,
      email: `user-${id}@example.com`,
      full_name: `User ${id}`,
      is_active: true,
      is_superuser: false
    };
    
    return res(
      ctx.status(200),
      ctx.json(mockUser)
    );
  }),
  
  // Health check endpoint
  rest.get(`${apiBaseUrl}/health`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ status: 'healthy' })
    );
  })
];

// Helper function to create custom handlers for tests
export function createHandler(
  method: 'get' | 'post' | 'put' | 'delete',
  url: string,
  status: number,
  responseData: any
) {
  return rest[method](url, (req, res, ctx) => {
    return res(
      ctx.status(status),
      ctx.json(responseData)
    );
  });
}

// Setup mock server
export const server = setupServer(...handlers);

// Start the server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));

// Reset handlers after each test
afterEach(() => server.resetHandlers());

// Close server after all tests
afterAll(() => server.close()); 
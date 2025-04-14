/**
 * User Service Test
 * 
 * This file tests the user service functionality for fetching and managing user data.
 */

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock API base URL
const API_BASE_URL = 'http://localhost:8000/api';

// User service to test
const userService = {
  getProfile: async () => {
    const response = await fetch(`${API_BASE_URL}/users/me`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    if (!response.ok) {
      throw new Error('Failed to fetch profile');
    }
    return response.json();
  },
  
  updateProfile: async (data: any) => {
    const response = await fetch(`${API_BASE_URL}/users/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      throw new Error('Failed to update profile');
    }
    return response.json();
  }
};

describe('User Service', () => {
  // Reset mocks before each test
  beforeEach(() => {
    jest.resetAllMocks();
    localStorage.clear();
    localStorage.setItem('token', 'fake-token');
  });

  describe('getProfile', () => {
    it('should fetch user profile successfully', async () => {
      // Mock successful response
      const mockUserData = {
        id: '1',
        email: 'user@example.com',
        full_name: 'Test User',
        is_active: true
      };
      
      // Setup mock response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockUserData
      });
      
      // Call the method
      const result = await userService.getProfile();
      
      // Assert the results
      expect(mockFetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/users/me`,
        expect.objectContaining({
          headers: {
            'Authorization': 'Bearer fake-token'
          }
        })
      );
      expect(result).toEqual(mockUserData);
    });

    it('should handle error when fetching profile fails', async () => {
      // Mock error response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized'
      });
      
      // Assert that the method throws an error
      await expect(userService.getProfile()).rejects.toThrow('Failed to fetch profile');
      
      // Verify the fetch call
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('updateProfile', () => {
    it('should update user profile successfully', async () => {
      // Profile data to update
      const updateData = {
        full_name: 'Updated Name',
        bio: 'New bio information'
      };
      
      // Mock successful response
      const mockUpdatedUser = {
        id: '1',
        email: 'user@example.com',
        full_name: 'Updated Name',
        bio: 'New bio information',
        is_active: true
      };
      
      // Setup mock response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockUpdatedUser
      });
      
      // Call the method
      const result = await userService.updateProfile(updateData);
      
      // Assert the results
      expect(mockFetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/users/me`,
        expect.objectContaining({
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer fake-token'
          },
          body: JSON.stringify(updateData)
        })
      );
      expect(result).toEqual(mockUpdatedUser);
    });

    it('should handle error when updating profile fails', async () => {
      // Profile data to update
      const updateData = {
        full_name: 'Invalid Name'
      };
      
      // Mock error response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request'
      });
      
      // Assert that the method throws an error
      await expect(userService.updateProfile(updateData)).rejects.toThrow('Failed to update profile');
      
      // Verify the fetch call
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });
}); 
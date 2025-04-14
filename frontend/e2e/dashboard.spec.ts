import { test, expect } from '@playwright/test';

test.describe('Dashboard Functionality', () => {
  // Mock authenticated state
  test.beforeEach(async ({ page }) => {
    // Set up a mock token in localStorage to simulate an authenticated user
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'mock_token');
      localStorage.setItem('user', JSON.stringify({
        id: '1',
        email: 'test@example.com',
        name: 'Test User'
      }));
    });
    
    // Navigate to the dashboard
    await page.goto('/dashboard');
  });
  
  test('should display user information in header', async ({ page }) => {
    // Check user name is displayed in the header
    await expect(page.getByText(/test user/i)).toBeVisible();
  });

  test('should show navigation menu items', async ({ page }) => {
    // Check main navigation items are visible
    await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /reports/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /settings/i })).toBeVisible();
  });

  test('should navigate to create report page', async ({ page }) => {
    // Click on the create report button
    await page.getByRole('link', { name: /create report/i }).click();
    
    // Verify navigation to the create report page
    await expect(page).toHaveURL(/\/reports\/create/);
    await expect(page.getByRole('heading', { name: /create report/i })).toBeVisible();
  });

  test('should display recent reports section', async ({ page }) => {
    // Check if recent reports section is visible
    await expect(page.getByRole('heading', { name: /recent reports/i })).toBeVisible();
  });

  test('should allow logout', async ({ page }) => {
    // Click on user menu to expand it
    await page.getByText(/test user/i).click();
    
    // Click on logout option
    await page.getByRole('button', { name: /log out/i }).click();
    
    // Verify redirection to login page
    await expect(page).toHaveURL(/\/login/);
  });
}); 
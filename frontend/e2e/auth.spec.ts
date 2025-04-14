import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Go to the login page before each test
    await page.goto('/login');
  });

  test('should show login form', async ({ page }) => {
    // Verify login form elements are present
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('should show validation errors for empty form submission', async ({ page }) => {
    // Click submit without entering any data
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Check for validation errors
    await expect(page.getByText(/email is required/i)).toBeVisible();
    await expect(page.getByText(/password is required/i)).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    // Enter invalid credentials
    await page.getByLabel(/email/i).fill('invalid@example.com');
    await page.getByLabel(/password/i).fill('wrongpassword');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Check for invalid credentials error
    await expect(page.getByText(/invalid email or password/i)).toBeVisible();
  });

  test('should navigate to registration page', async ({ page }) => {
    // Click on the registration link
    await page.getByRole('link', { name: /create an account/i }).click();
    
    // Verify we're on the registration page
    await expect(page).toHaveURL(/\/register/);
    await expect(page.getByRole('heading', { name: /create an account/i })).toBeVisible();
  });

  test('should navigate to forgot password page', async ({ page }) => {
    // Click on the forgot password link
    await page.getByRole('link', { name: /forgot password/i }).click();
    
    // Verify we're on the forgot password page
    await expect(page).toHaveURL(/\/forgot-password/);
    await expect(page.getByRole('heading', { name: /reset password/i })).toBeVisible();
  });
}); 
import { test, expect } from '@playwright/test';

test.describe('Reports Page Functionality', () => {
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
    
    // Mock API responses
    await page.route('**/api/v1/reports/list', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
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
    });
    
    await page.route('**/api/v1/reports/status/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'complete',
          result: {
            content: {
              executive_summary: '# Executive Summary\n\nThis is a test report.',
              key_metrics: '# Key Metrics\n\n- Metric 1: 42%\n- Metric 2: $1.2M'
            }
          }
        })
      });
    });
    
    // Navigate to the reports page
    await page.goto('/reports');
  });
  
  test('should display reports list', async ({ page }) => {
    // Check page title is rendered
    await expect(page.getByRole('heading', { name: 'Reports' })).toBeVisible();
    
    // Wait for the reports data to be visible
    await expect(page.getByText('Q2 Fundraising Overview')).toBeVisible();
    await expect(page.getByText('Donor Retention Analysis')).toBeVisible();
    
    // Check report types are displayed
    await expect(page.getByText('investor_update')).toBeVisible();
    await expect(page.getByText('knowledge_summary')).toBeVisible();
  });
  
  test('should switch between Recent and All tabs', async ({ page }) => {
    // Current tab should be Recent by default
    await expect(page.getByRole('button', { name: 'Recent' })).toHaveClass(/bg-blue-600/);
    
    // Switch to All tab
    await page.getByRole('button', { name: 'All' }).click();
    await expect(page.getByRole('button', { name: 'All' })).toHaveClass(/bg-blue-600/);
    
    // Switch back to Recent tab
    await page.getByRole('button', { name: 'Recent' }).click();
    await expect(page.getByRole('button', { name: 'Recent' })).toHaveClass(/bg-blue-600/);
  });
  
  test('should view report details', async ({ page }) => {
    // Click the View button on a report
    const viewButtons = page.getByRole('button', { name: 'View' });
    await viewButtons.first().click();
    
    // Check modal is shown with report content
    await expect(page.getByText('Executive Summary')).toBeVisible();
    await expect(page.getByText('This is a test report.')).toBeVisible();
    await expect(page.getByText('Key Metrics')).toBeVisible();
    await expect(page.getByText('Metric 1: 42%')).toBeVisible();
    
    // Close the modal
    await page.getByRole('button', { name: 'Close' }).click();
    await expect(page.getByText('Executive Summary')).not.toBeVisible();
  });
  
  test('should select and combine reports', async ({ page }) => {
    // Mock API for the combine endpoint
    await page.route('**/api/v1/reports/combine', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '3',
          title: 'Combined Report',
          status: 'processing',
          message: 'Report combination started'
        })
      });
    });
    
    // Select reports by clicking checkboxes
    const checkboxes = page.locator('input[type="checkbox"]');
    await checkboxes.nth(0).check();
    await checkboxes.nth(1).check();
    
    // Click the Combine Reports button
    await page.getByRole('button', { name: 'Combine Reports' }).click();
    
    // Check combine modal is displayed
    await expect(page.getByText('Combine Reports')).toBeVisible();
    
    // Enter a title and submit
    await page.getByLabel('Combined Report Title').fill('E2E Test Combined Report');
    await page.getByRole('button', { name: 'Combine Reports' }).last().click();
    
    // Check that the modal closes and we return to the reports page
    await expect(page.getByLabel('Combined Report Title')).not.toBeVisible();
  });
  
  test('should handle delete report action', async ({ page }) => {
    // Get initial count of reports
    const initialReportCount = await page.locator('tr').count() - 1; // Subtract header row
    
    // Click delete on the first report
    const deleteButtons = page.getByRole('button', { name: 'Delete' });
    await deleteButtons.first().click();
    
    // Check that the report was removed
    const finalReportCount = await page.locator('tr').count() - 1;
    expect(finalReportCount).toBeLessThan(initialReportCount);
  });
}); 
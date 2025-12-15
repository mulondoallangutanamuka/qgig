import { test, expect } from '@playwright/test';

test.describe('Institution Accept/Decline Interest E2E Test', () => {
  const PROFESSIONAL_EMAIL = 'sarah.nurse@gmail.com';
  const PROFESSIONAL_PASSWORD = 'password123';
  const INSTITUTION_EMAIL = 'nairobi.hospital@gmail.com';
  const INSTITUTION_PASSWORD = 'password123';
  const GIG_URL = '/gigs/1'; // Assuming a gig with ID 1 exists for testing

  test('should allow a professional to express interest and an institution to accept it', async ({ page }) => {
    // Step 1: Login as Professional
    await page.goto('/login');
    await page.fill('input[name="email"]', PROFESSIONAL_EMAIL);
    await page.fill('input[name="password"]', PROFESSIONAL_PASSWORD);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/browse_gigs');

    // Step 2: Open a gig and express interest
    await page.goto(GIG_URL);
    const expressInterestButton = page.locator('button:has-text("Express Interest")');
    await expressInterestButton.click();

    // Step 3: Assert button is disabled and success message is shown
    await expect(expressInterestButton).toBeDisabled();
    await expect(page.locator('text=Interest expressed successfully')).toBeVisible();

    // Step 4: Logout
    await page.goto('/logout');

    // Step 5: Login as Institution
    await page.goto('/login');
    await page.fill('input[name="email"]', INSTITUTION_EMAIL);
    await page.fill('input[name="password"]', INSTITUTION_PASSWORD);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/my_gigs');

    // Step 6: Open notifications panel
    await page.goto('/notifications');

    // Step 7: Assert notification with Accept/Decline buttons is visible
    const notification = page.locator('.notification-item').first();
    const acceptButton = notification.locator('button:has-text("Accept")');
    const declineButton = notification.locator('button:has-text("Decline")');
    await expect(acceptButton).toBeVisible();
    await expect(declineButton).toBeVisible();

    // Step 8: Click Accept
    await acceptButton.click();

    // Step 9: Assert buttons are disabled and status updates
    await expect(acceptButton).toBeDisabled();
    await expect(declineButton).toBeDisabled();
    await expect(notification.locator('text=Accepted')).toBeVisible();

    // Step 10: Logout
    await page.goto('/logout');

    // Step 11: Login as Professional to check for response notification
    await page.goto('/login');
    await page.fill('input[name="email"]', PROFESSIONAL_EMAIL);
    await page.fill('input[name="password"]', PROFESSIONAL_PASSWORD);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/browse_gigs');

    // Step 12: Check notifications for acceptance
    await page.goto('/notifications');
    const responseNotification = page.locator('.notification-item:has-text("Interest Accepted")');
    await expect(responseNotification).toBeVisible();
  });
});

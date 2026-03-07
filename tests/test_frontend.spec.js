// Playwright UI tests for frontend

const { test, expect } = require('@playwright/test');

test.describe('TrustGraph Frontend', () => {
  
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    await expect(page).toHaveTitle(/TrustGraph/);
    await expect(page.locator('h1')).toContainText('TrustGraph');
  });
  
  test('login flow works', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Enter phone number
    await page.fill('#phoneInput', '9876543210');
    await page.click('button:has-text("OTP भेजें")');
    
    // Wait for OTP section
    await expect(page.locator('#otpSection')).toBeVisible();
    
    // Enter OTP
    await page.fill('#otpInput', '123456');
    await page.click('button:has-text("सत्यापित करें")');
    
    // Should navigate to dashboard
    await expect(page.locator('#dashboard')).toBeVisible();
  });
  
  test('voice button is accessible', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Login first
    await page.fill('#phoneInput', '9876543210');
    await page.click('button:has-text("OTP भेजें")');
    await page.fill('#otpInput', '123456');
    await page.click('button:has-text("सत्यापित करें")');
    
    // Check voice button
    const voiceBtn = page.locator('#voiceBtn');
    await expect(voiceBtn).toBeVisible();
    await expect(voiceBtn).toHaveAttribute('aria-label');
  });
  
  test('navigation works', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Login
    await page.fill('#phoneInput', '9876543210');
    await page.click('button:has-text("OTP भेजें")');
    await page.fill('#otpInput', '123456');
    await page.click('button:has-text("सत्यापित करें")');
    
    // Test navigation
    await page.click('button:has-text("प्रमाणपत्र")');
    await expect(page.locator('#credentialsScreen')).toBeVisible();
    
    await page.click('button:has-text("←")');
    await expect(page.locator('#dashboard')).toBeVisible();
  });
  
  test('theme selector works', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Login
    await page.fill('#phoneInput', '9876543210');
    await page.click('button:has-text("OTP भेजें")');
    await page.fill('#otpInput', '123456');
    await page.click('button:has-text("सत्यापित करें")');
    
    // Open theme selector
    await page.click('.nav-btn:has-text("सेटिंग")');
    await expect(page.locator('#themeSelector')).toBeVisible();
    
    // Select dark theme
    await page.click('button:has-text("डार्क मोड")');
    
    // Check theme applied
    const html = page.locator('html');
    await expect(html).toHaveAttribute('data-theme', 'dark');
  });
  
  test('keyboard navigation works', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Tab through elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Check focus visible
    const focused = page.locator(':focus');
    await expect(focused).toBeVisible();
  });
  
  test('mobile responsive', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('http://localhost:3000');
    
    // Check mobile layout
    await expect(page.locator('.header')).toBeVisible();
    await expect(page.locator('.card')).toBeVisible();
  });
  
  test('accessibility - ARIA labels', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Check ARIA labels present
    const voiceBtn = page.locator('#voiceBtn');
    await expect(voiceBtn).toHaveAttribute('aria-label');
    await expect(voiceBtn).toHaveAttribute('aria-pressed');
  });
  
  test('performance - page load time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('http://localhost:3000');
    const loadTime = Date.now() - startTime;
    
    // Should load in under 2 seconds
    expect(loadTime).toBeLessThan(2000);
  });
});

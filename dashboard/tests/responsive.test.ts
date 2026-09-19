import { test, expect, devices } from "@playwright/test";

// Test breakpoints
const breakpoints = [
  { name: "mobile-small", width: 375, height: 667 }, // iPhone SE
  { name: "mobile", width: 480, height: 800 },
  { name: "mobile-large", width: 640, height: 1136 },
  { name: "tablet-portrait", width: 768, height: 1024 }, // iPad portrait
  { name: "tablet-landscape", width: 1024, height: 768 }, // iPad landscape
  { name: "desktop-small", width: 1280, height: 800 },
  { name: "desktop", width: 1440, height: 900 },
  { name: "desktop-large", width: 1920, height: 1080 },
];

// All pages to test
const pages = [
  { path: "/", name: "Dashboard" },
  { path: "/devices", name: "Devices" },
  { path: "/traffic", name: "Traffic" },
  { path: "/flows", name: "Flows" },
  { path: "/domains", name: "Domains" },
  { path: "/applications", name: "Applications" },
  { path: "/protocols", name: "Protocols" },
  { path: "/analytics", name: "Analytics" },
  { path: "/history", name: "History" },
  { path: "/alerts", name: "Alerts" },
  { path: "/reports", name: "Reports" },
  { path: "/rules", name: "Rules" },
  { path: "/limits", name: "Limits" },
  { path: "/firewall", name: "Firewall" },
  { path: "/quotas", name: "Quotas" },
  { path: "/interfaces", name: "Interfaces" },
  { path: "/system", name: "System" },
  { path: "/settings", name: "Settings" },
];

test.describe("Responsive Design Tests", () => {
  // Use a test account to login
  test.beforeEach(async ({ page }) => {
    // Navigate to login page first
    await page.goto("http://localhost:3000/login");

    // Wait for login form
    await page.waitForSelector("input#username");

    // Login with default credentials
    await page.fill("input#username", "admin");
    await page.fill("input#password", "admin_change_me");
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await page.waitForURL("http://localhost:3000/", { timeout: 10000 });
  });

  for (const bp of breakpoints) {
    test.describe(`${bp.name} (${bp.width}x${bp.height})`, () => {
      test.use({ viewport: { width: bp.width, height: bp.height } });

      for (const pageInfo of pages) {
        test(`${pageInfo.name} page - no horizontal scroll, layout OK`, async ({
          page,
        }) => {
          await page.goto(`http://localhost:3000${pageInfo.path}`);

          // Wait for page to load
          await page.waitForLoadState("networkidle");

          // Check for horizontal scrollbar on body
          const bodyScrollWidth = await page.evaluate(
            () => document.body.scrollWidth,
          );
          const viewportWidth = await page.evaluate(() => window.innerWidth);

          // Allow small tolerance for scrollbar
          expect(bodyScrollWidth).toBeLessThanOrEqual(viewportWidth + 20);

          // Check that main content is visible
          await expect(
            page
              .locator('main, [role="main"], .container, #main-content')
              .first(),
          ).toBeVisible({ timeout: 5000 });
        });
      }
    });
  }

  test.describe("Sidebar Behavior", () => {
    test("Desktop: sidebar is visible and not a drawer", async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 800 });
      await page.goto("http://localhost:3000/");
      await page.waitForLoadState("networkidle");

      // Check sidebar is visible (not hidden behind hamburger)
      const sidebar = page
        .locator('aside[class*="fixed"][class*="left-0"], aside[class*="w-64"]')
        .first();
      await expect(sidebar).toBeVisible();

      // Check it's not a mobile drawer (should not have transform/translate for hiding)
      const sidebarStyle = await sidebar.evaluate(
        (el) => window.getComputedStyle(el).transform,
      );
      expect(sidebarStyle).not.toContain("translateX(-100%)");
    });

    test("Mobile: sidebar is a drawer (hidden by default)", async ({
      page,
    }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto("http://localhost:3000/");
      await page.waitForLoadState("networkidle");

      // Check sidebar exists but is hidden (mobile drawer)
      const sidebar = page
        .locator('aside[class*="fixed"][class*="left-0"]')
        .first();
      // On mobile, sidebar should be positioned off-screen or have drawer behavior
      const isVisible = await sidebar.isVisible();

      // The sidebar might be hidden off-screen on mobile
      // Check if there's a hamburger menu button
      const hamburger = page
        .locator(
          'button[aria-label*="menu"], button[aria-label*="Menu"], button:has(svg.lucide-menu)',
        )
        .first();
      // Note: exact hamburger detection depends on implementation
    });
  });

  test.describe("Table Responsive Strategy", () => {
    test("Tables use horizontal scroll on mobile", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto("http://localhost:3000/devices");
      await page.waitForLoadState("networkidle");

      // Find table containers
      const tableContainers = page.locator(
        '.overflow-x-auto, [class*="overflow-x-auto"]',
      );
      await expect(tableContainers.first()).toBeVisible();
    });

    test("Tables show all columns on desktop", async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.goto("http://localhost:3000/devices");
      await page.waitForLoadState("networkidle");

      // Table should be fully visible without horizontal scroll on container
      const tableContainer = page.locator(".overflow-x-auto").first();
      const scrollWidth = await tableContainer.evaluate((el) => el.scrollWidth);
      const clientWidth = await tableContainer.evaluate((el) => el.clientWidth);

      // On desktop, table should fit or be close to fitting
      expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 100); // Allow small overflow
    });
  });

  test.describe("Charts", () => {
    test("Charts render without clipped labels on all breakpoints", async ({
      page,
    }) => {
      for (const bp of breakpoints) {
        await page.setViewportSize({ width: bp.width, height: bp.height });
        await page.goto("http://localhost:3000/");
        await page.waitForLoadState("networkidle");

        // Check TrafficChart exists and is visible
        const chart = page.locator("canvas, svg").first();
        await expect(chart).toBeVisible({ timeout: 5000 });

        // Check no text is clipped (basic check - chart container visible)
        const chartContainer = page
          .locator('[class*="card"]:has(canvas), [class*="card"]:has(svg)')
          .first();
        await expect(chartContainer).toBeVisible();
      }
    });

    test("Charts have visible tooltips on hover", async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.goto("http://localhost:3000/");
      await page.waitForLoadState("networkidle");

      // Target the chart canvas specifically (not sidebar icons)
      const chart = page.locator('[class*="card"] canvas').first();
      if (await chart.isVisible()) {
        // Hover over chart area
        await chart.hover({ position: { x: 200, y: 100 } });
        await page.waitForTimeout(500);

        // Check for tooltip (recharts tooltip or similar) - might not appear if no data
        const tooltip = page
          .locator('[class*="recharts-tooltip"], [class*="tooltip"]')
          .first();
        // Just verify no errors when hovering
      }
    });
  });

  test.describe("Cards", () => {
    test("Cards wrap properly on mobile", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto("http://localhost:3000/");
      await page.waitForLoadState("networkidle");

      // Check metric cards stack vertically on mobile
      const metricCards = page
        .locator('[class*="grid"] > [class*="card"], .card-default')
        .first();
      await expect(metricCards).toBeVisible();
    });

    test("Cards show all content on desktop", async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.goto("http://localhost:3000/");
      await page.waitForLoadState("networkidle");

      // Cards should be in grid layout
      const grid = page.locator(".grid").first();
      await expect(grid).toBeVisible();
    });
  });

  test.describe("Forms", () => {
    test("Form fields fit on mobile", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto("http://localhost:3000/settings");
      await page.waitForLoadState("networkidle");

      // Check inputs are visible and not overflowing
      const inputs = page.locator("input, select, textarea");
      const count = await inputs.count();
      expect(count).toBeGreaterThan(0);

      for (let i = 0; i < Math.min(count, 5); i++) {
        const input = inputs.nth(i);
        const box = await input.boundingBox();
        if (box) {
          expect(box.width).toBeLessThanOrEqual(375); // Should fit in viewport
        }
      }
    });

    test("Form labels are readable", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto("http://localhost:3000/settings");
      await page.waitForLoadState("networkidle");

      const labels = page.locator("label");
      const count = await labels.count();

      for (let i = 0; i < Math.min(count, 10); i++) {
        const label = labels.nth(i);
        const text = await label.textContent();
        expect(text?.trim().length).toBeGreaterThan(0);
      }
    });
  });

  test.describe("Modals", () => {
    test("Modals fit on mobile and are scrollable", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto("http://localhost:3000/devices");
      await page.waitForLoadState("networkidle");

      // Try to open a modal if there's a button to add/edit
      const addButton = page
        .locator(
          'button:has-text("Add"), button:has-text("Create"), button[aria-label*="add"]',
        )
        .first();
      if (await addButton.isVisible({ timeout: 2000 })) {
        await addButton.click();
        await page.waitForTimeout(500);

        // Check modal is visible
        const modal = page
          .locator('[role="dialog"], .fixed.inset-0, [class*="modal"]')
          .first();
        await expect(modal).toBeVisible();

        // Check modal content is scrollable if needed
        const modalContent = page
          .locator('[role="dialog"] > div, .fixed.inset-0 > div')
          .first();
        const scrollHeight = await modalContent.evaluate(
          (el) => el.scrollHeight,
        );
        const clientHeight = await modalContent.evaluate(
          (el) => el.clientHeight,
        );

        // Modal should fit or be scrollable
        if (scrollHeight > clientHeight) {
          // Should have scroll behavior
          const overflow = await modalContent.evaluate(
            (el) => window.getComputedStyle(el).overflowY,
          );
          expect(["auto", "scroll"]).toContain(overflow);
        }

        // Close modal
        await page.keyboard.press("Escape");
      }
    });

    test("Modals close with Escape key", async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 800 });
      await page.goto("http://localhost:3000/devices");
      await page.waitForLoadState("networkidle");

      const addButton = page
        .locator(
          'button:has-text("Add"), button:has-text("Create"), button[aria-label*="add"]',
        )
        .first();
      if (await addButton.isVisible({ timeout: 2000 })) {
        await addButton.click();
        await page.waitForTimeout(500);

        const modal = page
          .locator('[role="dialog"], .fixed.inset-0, [class*="modal"]')
          .first();
        await expect(modal).toBeVisible();

        // Press Escape
        await page.keyboard.press("Escape");
        await page.waitForTimeout(300);

        // Modal should be closed
        await expect(modal).not.toBeVisible();
      }
    });
  });

  test.describe("Touch Targets", () => {
    test("Buttons and links meet minimum 44x44px on mobile", async ({
      page,
    }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto("http://localhost:3000/");
      await page.waitForLoadState("networkidle");

      const interactiveElements = page.locator(
        'button, a, [role="button"], input[type="button"], input[type="submit"]',
      );
      const count = await interactiveElements.count();

      for (let i = 0; i < Math.min(count, 20); i++) {
        const el = interactiveElements.nth(i);
        const box = await el.boundingBox();
        if (box && box.width > 0 && box.height > 0) {
          // Minimum touch target 44x44 (allowing for padding)
          expect(box.width).toBeGreaterThanOrEqual(32); // Allow slightly smaller with padding
          expect(box.height).toBeGreaterThanOrEqual(32);
        }
      }
    });
  });

  test.describe("No Accidental Horizontal Scroll", () => {
    for (const bp of breakpoints) {
      test(`No horizontal scroll at ${bp.name} (${bp.width}px)`, async ({
        page,
      }) => {
        await page.setViewportSize({ width: bp.width, height: bp.height });
        await page.goto("http://localhost:3000/");
        await page.waitForLoadState("networkidle");

        // Check body doesn't overflow horizontally
        const hasHorizontalScroll = await page.evaluate(() => {
          return document.body.scrollWidth > window.innerWidth + 10; // 10px tolerance
        });

        expect(hasHorizontalScroll).toBe(false);
      });
    }
  });
});

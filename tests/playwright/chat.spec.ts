import { test, expect } from "@playwright/test";

test.describe("Knowledge Base Agent Chat UI", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/chat");
    // Wait for Gradio to fully load (textarea appears)
    await page.waitForSelector("textarea", { timeout: 15_000 });
  });

  test("1. Page loads with title and input", async ({ page }) => {
    // Title is visible
    await expect(page.locator("text=Knowledge Base Agent")).toBeVisible();

    // Chat input textarea is present and enabled
    const input = page.locator("textarea");
    await expect(input).toBeVisible();
    await expect(input).toBeEnabled();

    // Submit button exists (Gradio uses .submit-button class)
    const submitBtn = page.locator("button.submit-button");
    await expect(submitBtn).toBeVisible();
  });

  test("2. Chat fills viewport height (no dead space)", async ({ page }) => {
    // The chatbot bubble-wrap container should take up most of the viewport
    const chatbot = page.locator(".bubble-wrap").first();
    await expect(chatbot).toBeVisible();

    const viewport = page.viewportSize()!;
    const box = await chatbot.boundingBox();
    expect(box).not.toBeNull();

    // Chatbot should occupy at least 55% of viewport height
    expect(box!.height).toBeGreaterThan(viewport.height * 0.55);
  });

  test("3. Can submit a question and receive a response", async ({ page }) => {
    const input = page.locator("textarea");
    await input.fill("how important is hydration?");

    const submitBtn = page.locator("button.submit-button");
    await submitBtn.click();

    // Wait for a response message row to appear
    const responseRow = page.locator(".message-row.bot-row").first();
    await expect(responseRow).toBeVisible({ timeout: 45_000 });

    // Response should contain substantive text
    const text = await responseRow.textContent();
    expect(text!.length).toBeGreaterThan(50);
  });

  test("4. Response includes source links", async ({ page }) => {
    const input = page.locator("textarea");
    await input.fill("how important is hydration?");

    const submitBtn = page.locator("button.submit-button");
    await submitBtn.click();

    // Wait for source links to appear
    const sourceLink = page.locator('a[href*="pmc.ncbi.nlm.nih.gov"]').first();
    await expect(sourceLink).toBeVisible({ timeout: 45_000 });

    // Verify the link is a valid PMC URL
    const href = await sourceLink.getAttribute("href");
    expect(href).toMatch(/pmc\.ncbi\.nlm\.nih\.gov\/articles\/PMC\d+/);
  });

  test("5. Sources section has a visual separator from the answer", async ({
    page,
  }) => {
    const input = page.locator("textarea");
    await input.fill("how important is hydration?");

    const submitBtn = page.locator("button.submit-button");
    await submitBtn.click();

    // Wait for response
    await page.locator('a[href*="pmc.ncbi.nlm.nih.gov"]').first().waitFor({
      timeout: 45_000,
    });

    // The response should contain "Sources:" text (rendered from markdown)
    const sourcesHeader = page.locator("text=Sources:").first();
    await expect(sourcesHeader).toBeVisible();

    // There should be an <hr> separator (from markdown ---)
    const hr = page.locator(".bot-row hr").first();
    await expect(hr).toBeVisible();
  });

  test("6. Textarea clears after submission", async ({ page }) => {
    const input = page.locator("textarea");
    await input.fill("test question about exercise");

    const submitBtn = page.locator("button.submit-button");
    await submitBtn.click();

    // After submission, textarea should be cleared
    await expect(input).toHaveValue("", { timeout: 5_000 });

    // Wait for response to confirm the message was sent
    const responseRow = page.locator(".message-row.bot-row").last();
    await expect(responseRow).toBeVisible({ timeout: 45_000 });
  });

  test("7. Health API endpoint returns 200", async ({ request }) => {
    const response = await request.get("/health");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("healthy");
  });
});

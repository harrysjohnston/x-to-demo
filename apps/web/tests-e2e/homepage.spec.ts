import { expect, test } from "@playwright/test";

test.describe("Homepage", () => {
  test("loads successfully", async ({ page }) => {
    await page.goto("/");
    // Check that the page loaded (has the main element)
    await expect(page.getByRole("main")).toBeVisible();
  });

  test("displays the main heading", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: /Turn input X into a runnable demo code spec/i }),
    ).toBeVisible();
  });

  test("displays the description text", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText(/Upload or paste brainstorming input/i)).toBeVisible();
  });

  test("displays the pipeline controls", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("textbox", { name: "Input X" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Run pipeline" })).toBeVisible();
  });
});

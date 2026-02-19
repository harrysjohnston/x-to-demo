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

  test("displays the auth form", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in" }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Create account" })).toBeVisible();
  });
});

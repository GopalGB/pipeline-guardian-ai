import { test, expect } from "@playwright/test";

test("golden flow uses the deterministic test backend", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Operator recovery desk")).toBeVisible();
});


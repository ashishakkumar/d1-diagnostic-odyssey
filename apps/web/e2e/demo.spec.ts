import { expect, test } from "@playwright/test";
import path from "node:path";

const shots = path.resolve(__dirname, "../../../docs/demo-screenshots");

test("five synthetic cases, the comparison, and the stop screen", async ({ page }) => {
  await page.goto("/notebook");
  await page.getByLabel("Your name for this notebook").fill("ashish");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("button", { name: "Load Separated rows" })).toBeVisible();
  await page.screenshot({ path: path.join(shots, "01-cases.png"), fullPage: true });

  await page.getByRole("button", { name: "Load Separated rows" }).click();
  await expect(page.getByTestId("comparison")).toContainText("ORPHA:9000001");
  await expect(page.getByTestId("public-ranker")).toContainText(
    "beats the degree baseline at k=1 and k=5",
  );
  await expect(page.getByTestId("public-ranker")).toContainText("synthetic frequency-bin card");
  await expect(page.getByText("ratio of zero").first()).toBeVisible();
  await expect(page.getByText("long for the hand").first()).toBeVisible();
  await expect(page.getByRole("contentinfo")).toContainText("112");
  await expect(page.getByText("This is not a diagnosis").first()).toBeVisible();
  await page.screenshot({ path: path.join(shots, "02-separated.png"), fullPage: true });

  await page.goto("/notebook");
  await page.getByRole("button", { name: "Load No separated row" }).click();
  await expect(page.getByText("did not separate a first row").first()).toBeVisible();
  await expect(page.getByText("does not mean you are well").first()).toBeVisible();
  await expect(page.getByTestId("comparison")).not.toContainText("Margin");
  await page.screenshot({ path: path.join(shots, "03-abstain.png"), fullPage: true });

  await page.goto("/notebook");
  await page.getByRole("button", { name: "Load Stable at both ends" }).click();
  await expect(page.getByTestId("comparison")).toContainText("ORPHA:9000011");
  await expect(page.getByText(/Margin /).first()).toBeVisible();
  await page.screenshot({ path: path.join(shots, "04-stable.png"), fullPage: true });

  await page.goto("/notebook");
  await page.getByRole("button", { name: "Load Variant does not move the comparison" }).click();
  await expect(page.getByTestId("comparison")).toContainText("ORPHA:9000001");
  await page.getByRole("checkbox", { name: "Show the experimental population prior" }).check();
  await expect(page.getByTestId("population-prior")).toContainText("0.00012");
  await expect(page.getByTestId("population-prior")).toContainText("did not call gnomAD");
  await page.screenshot({ path: path.join(shots, "05-prior.png"), fullPage: true });

  await page.goto("/notebook");
  await page.getByRole("button", { name: "Load No dose on this page" }).click();
  await expect(page.getByText("does not choose a dose").first()).toBeVisible();
  await page.screenshot({ path: path.join(shots, "06-limits.png"), fullPage: true });

  await page.getByRole("link", { name: "Lab variant" }).click();
  await page.getByRole("button", { name: "Try a warning-sign phrase" }).click();
  await expect(page.getByText("Stop")).toBeVisible();
  await expect(page.getByText(/Unconsciousness/)).toBeVisible();
  await page.screenshot({ path: path.join(shots, "07-stop.png"), fullPage: true });
});

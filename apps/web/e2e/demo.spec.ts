import { expect, test } from "@playwright/test";
import path from "node:path";

const shots = path.resolve(__dirname, "../../../docs/demo-screenshots");

test("one step, then the software reads a synthetic note", async ({ page }) => {
  test.setTimeout(90_000);
  await page.goto("/");
  await expect(page.getByLabel("Your name for this notebook")).toHaveCount(0);
  await expect(page.getByTestId("pipeline")).toBeVisible();
  await expect(page.getByTestId("what-is-this-body")).toBeHidden();
  await expect(page.getByTestId("method")).toContainText("No language model ran");
  await expect(page.getByTestId("stage-read")).toContainText("Rule");
  await expect(page.getByTestId("stage-rank")).toContainText("Scoring model");
  await expect(page.getByRole("contentinfo")).toContainText("112");
  await expect(page.getByTestId("tour")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId("tour-step")).toContainText("1 of 5");
  await expect(page.getByTestId("tour-step")).toContainText("Rule");
  await page.screenshot({ path: path.join(shots, "01-cases.png"), fullPage: true });
  await page.locator("summary", { hasText: "What is this?" }).click();
  await expect(page.getByTestId("what-is-this-body")).toContainText("Read, Map, and Match are rules");
  await expect(page.getByTestId("what-is-this-body")).toContainText("scoring model");
  const tourCard = page.getByTestId("tour-card");
  await tourCard.getByRole("button", { name: "Next", exact: true }).click();
  await expect(tourCard.getByRole("button", { name: "Next", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Correct" }).first().click();
  await expect(tourCard.getByRole("button", { name: "Next", exact: true })).toBeEnabled();
  await tourCard.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByRole("button", { name: "Restore" }).click();
  await expect(page.getByTestId("tour-step")).toContainText("Rule");
  await tourCard.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByTestId("tour-step")).toContainText("Scoring model");
  await tourCard.getByRole("button", { name: "Next", exact: true }).click();
  await tourCard.getByRole("button", { name: "Done", exact: true }).click();
  await expect(page.getByTestId("tour")).toHaveCount(0);
  await page.getByTestId("take-tour").click();
  await expect(page.getByTestId("tour")).toBeVisible();
  await page.getByTestId("tour-card").getByRole("button", { name: "Skip", exact: true }).click();
  await expect(page.getByTestId("tour")).toHaveCount(0);

  await expect(page.getByTestId("stage-map")).toContainText("Map");
  await expect(page.getByTestId("stage-match")).toContainText("Match");
  await expect(page.getByTestId("stage-rank")).toContainText("Rank");
  await expect(page.getByTestId("actor-software").first()).toContainText("Software, not a person.");
  await expect(page.getByTestId("stage-caption")).toContainText("What the software did");
  await expect(page.getByTestId("stage-caption")).toContainText("What you decide");
  await expect(page.getByRole("button", { name: "Confirm these terms" })).toBeVisible();
  await expect(page.getByTestId("note")).toContainText("long fingers");
  await expect(page.getByTestId("chips")).toContainText("HP:0001166");
  await expect(page.getByTestId("chips")).toContainText("Quote:");
  await expect(page.getByTestId("match-grid")).toContainText("ORPHA:9000001");
  await expect(page.getByTestId("ranks")).toContainText("ORPHA:9000001");
  await expect(page.getByTestId("questions")).toContainText("Ask a doctor");
  await expect(page.getByTestId("actor-person")).toContainText("You decide");
  await expect(page.getByTestId("impact")).toContainText("opened with the page");
  await expect(page.getByTestId("impact")).toContainText("a name, Continue, and Load");
  await expect(page.getByText("This is not a diagnosis").first()).toBeVisible();
  await expect(page.getByRole("contentinfo")).toContainText("112");
  await page.getByRole("button", { name: "Confirm these terms" }).click();
  await expect(page.getByTestId("recorded")).toContainText("synthetic-reader");
  await page.screenshot({ path: path.join(shots, "02-separated.png"), fullPage: true });

  await page.goto("/?slug=abstain");
  await expect(page.getByTestId("abstain")).toContainText("Not enough signal", { timeout: 15_000 });
  await expect(page.getByText("does not mean you are well").first()).toBeVisible();
  await expect(page.getByTestId("match-grid")).toContainText("ORPHA:9000026");
  await expect(page.getByTestId("ranks")).toHaveCount(0);
  await page.screenshot({ path: path.join(shots, "03-abstain.png"), fullPage: true });

  await page.goto("/?slug=stable");
  await expect(page.getByTestId("abstain")).toContainText("Not enough signal", { timeout: 15_000 });
  await expect(page.getByTestId("ranks")).toContainText("ORPHA:9000011");
  await expect(page.getByTestId("ranks")).toContainText("ORPHA:9000012");
  await page.screenshot({ path: path.join(shots, "04-stable.png"), fullPage: true });

  await page.goto("/?slug=variant");
  await expect(page.getByText("Resnik did not use it").first()).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId("ranks")).toContainText("ORPHA:9000001");
  await page.screenshot({ path: path.join(shots, "05-prior.png"), fullPage: true });

  await page.goto("/?slug=limits");
  await expect(page.getByText("does not choose a dose").first()).toBeVisible({ timeout: 15_000 });
  await page.screenshot({ path: path.join(shots, "06-limits.png"), fullPage: true });

  await page.goto("/");
  await page.locator("summary", { hasText: "Another synthetic note" }).click();
  await page.getByRole("textbox", { name: "Synthetic note" }).fill("Unconsciousness.");
  await page.getByRole("button", { name: "Read this note" }).click();
  await expect(page.getByTestId("stop")).toContainText("Stop");
  await expect(page.getByTestId("stop")).toContainText("Unconsciousness");
  await expect(page.getByTestId("stop")).toContainText("112");
  await page.screenshot({ path: path.join(shots, "07-stop.png"), fullPage: true });

  await page.goto("/");
  await page.locator("summary", { hasText: "Another synthetic note" }).click();
  await page.getByLabel("Upload a synthetic note").setInputFiles({
    name: "note.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Synthetic note. The hands show long fingers."),
  });
  await expect(page.getByTestId("chips")).toContainText("HP:0001166", { timeout: 15_000 });
  await expect(page.getByTestId("method")).toContainText("No language model ran");
});

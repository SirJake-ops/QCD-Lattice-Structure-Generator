import { test, expect } from "@playwright/test";
import type { Job, Model } from "../src/types";

test("local browser submits, inspects, rotates, and cancels experiments", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Explore the force between quarks." }),
  ).toBeVisible();
  await expect(page.getByText("CPU simulator ready")).toBeVisible();
  await page.getByLabel("Samples / chain").fill("16");
  await page.getByLabel("Warm-up sweeps").fill("10");
  await page.getByRole("button", { name: "Run simulation" }).click();
  await expect(page.locator(".run-strip .run-state")).toHaveText("completed", {
    timeout: 30000,
  });
  await expect(page.getByText("Download artifact manifest")).toBeVisible();
  await expect(page.locator(".diagnostics dd").first()).not.toHaveText("—");
  await page.locator("#time").fill("2");
  await expect(page.getByText("t/a = 2")).toBeVisible();
  const canvas = page.locator(".lattice-canvas canvas");
  await expect(canvas).toBeVisible();
  const rect = await canvas.boundingBox();
  if (rect) {
    await page.mouse.move(rect.x + rect.width / 2, rect.y + rect.height / 2);
    await page.mouse.down();
    await page.mouse.move(
      rect.x + rect.width / 2 + 70,
      rect.y + rect.height / 2 + 30,
      { steps: 8 },
    );
    await page.mouse.up();
  }
  await page.screenshot({
    path: "/tmp/qcd-explorer-desktop.png",
    fullPage: true,
  });
  await page.getByLabel("Warm-up sweeps").fill("100000");
  await page.getByRole("button", { name: "Run simulation" }).click();
  await expect(page.getByRole("button", { name: "Cancel job" })).toBeVisible();
  await page.getByRole("button", { name: "Cancel job" }).click();
  await expect(page.locator(".run-strip .run-state")).toHaveText("cancelled");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "/tmp/qcd-explorer-mobile.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect(errors).toEqual([]);
});

test("measured corpus compares all three potentials and displays a real field map", async ({
  page,
  request,
}) => {
  const models: Model[] = await (await request.get("/api/v1/models")).json();
  const jobs: Job[] = await (await request.get("/api/v1/jobs")).json();
  const measured = jobs.find(
    (j) =>
      j.state === "completed" &&
      j.request.beta === 1.5 &&
      j.request.extents.join(",") === "8,8,8,24",
  );
  test.skip(
    !models.length || !measured,
    "Generate the measured pilot corpus and train a model to exercise this test",
  );
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await page
    .getByRole("row")
    .filter({ hasText: measured!.id.slice(0, 10) })
    .getByRole("button", { name: "Inspect" })
    .click();
  await expect(page.getByText("Download artifact manifest")).toBeVisible();
  await page.getByLabel("Potential separation").selectOption("3");
  await page.getByRole("button", { name: "Fast prediction" }).click();
  await expect(
    page.getByRole("heading", { name: "How well does the model predict?" }),
  ).toBeVisible();
  for (const card of [".measured", ".formula", ".learned"]) {
    await expect(
      page.locator(`.result-card${card} .result-value`),
    ).not.toContainText("—");
    await expect(
      page.locator(`.result-card${card} .result-value small`),
    ).toHaveText("ΔaV");
  }
  await page.screenshot({
    path: "/tmp/qcd-explorer-prediction.png",
    fullPage: true,
  });
  const field = jobs.find(
    (j) =>
      j.state === "completed" &&
      j.request.beta === 1.6 &&
      j.request.measure_field &&
      j.request.field_t === 11,
  );
  if (field) {
    await page
      .getByRole("row")
      .filter({ hasText: field.id.slice(0, 10) })
      .getByRole("button", { name: "Inspect" })
      .click();
    await expect(page.locator(".field-panel .plot")).toBeVisible();
    await page
      .getByRole("button", { name: "Uncertainty", exact: true })
      .click();
    await page.screenshot({
      path: "/tmp/qcd-explorer-field.png",
      fullPage: true,
    });
  }
  expect(errors).toEqual([]);
});

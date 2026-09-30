import { expect, test } from "@playwright/test";

/**
 * The complete player journey, against the real backend and database:
 * sign up -> pick a round -> answer all 10 questions -> see the result -> history -> log out.
 *
 * This also guards a real bug found during manual testing: clicking "Start a Round"
 * while logged out (which Next.js prefetches) used to bounce a freshly-registered
 * player straight back to the login page, because the client-side navigation replayed
 * the cached "you must log in" redirect instead of asking the server again. The fix
 * was a full page reload after login/registration/logout (see src/lib/navigation.ts).
 * Reproducing the exact sequence a player takes - landing page first, not /login
 * directly - is what would catch a regression of that bug.
 */

function uniquePlayer() {
  const id = `${Date.now()}_${Math.floor(Math.random() * 10_000)}`;
  return { username: `e2e_${id}`, email: `e2e_${id}@example.com`, password: "a long password" };
}

test("a full round, start to finish", async ({ page }) => {
  const player = uniquePlayer();

  await test.step("landing page, logged out", async () => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /what would.*you.*do/i })).toBeVisible();
  });

  await test.step("Start a Round sends a logged-out visitor to log in", async () => {
    await page.getByRole("link", { name: /start a round/i }).first().click();
    await expect(page).toHaveURL(/\/login\?next=%2Fplay/);
  });

  await test.step("sign up, and land on /play (not bounced back to login)", async () => {
    await page.getByRole("link", { name: /create an account/i }).click();
    await expect(page).toHaveURL(/\/register/);

    await page.getByLabel("Username").fill(player.username);
    await page.getByLabel("Email").fill(player.email);
    await page.getByLabel("Password").fill(player.password);
    await page.getByRole("button", { name: /create account/i }).click();

    await expect(page).toHaveURL(/\/play$/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { name: /choose your round/i })).toBeVisible();
  });

  await test.step("only Random is playable with 24 seeded scenarios", async () => {
    await expect(page.getByRole("button", { name: /^random/i })).toBeEnabled();
    await expect(page.getByText("Coming soon")).toHaveCount(8);
  });

  let roundUrl = "";
  await test.step("start a round", async () => {
    await page.getByRole("button", { name: /^random/i }).click();
    await expect(page).toHaveURL(/\/play\/[0-9a-f-]{36}$/);
    roundUrl = page.url();
    await expect(page.getByRole("progressbar")).toBeVisible();
  });

  await test.step("answer all 10 questions", async () => {
    for (let n = 1; n <= 10; n++) {
      await expect(page.getByText(`Question ${n}`).first()).toBeVisible();
      await expect(page.getByText("What do you do?")).toBeVisible();

      if (n === 5) {
        // The server, not the browser, is the source of truth for round progress:
        // reloading BEFORE answering must land back on this same still-open question.
        await page.reload();
        await expect(page.getByText(`Question ${n}`).first()).toBeVisible();
        await expect(page.getByText("What do you do?")).toBeVisible();
      }

      // Mix input methods: mostly keyboard, one click, to exercise both paths.
      if (n === 3) {
        await page.getByRole("button", { name: /^option b/i }).click();
      } else {
        await page.keyboard.press(["a", "b", "c"][n % 3]);
      }

      await expect(page.getByText("How everyone else answered")).toBeVisible();
      // Whatever the sample size, the numbers must never be invented: either an
      // honest "not enough data" message, or percentages that add to exactly 100.
      const unavailable = page.getByTestId("crowd-unavailable");
      if (await unavailable.isVisible()) {
        await expect(unavailable).toContainText("Not enough responses yet.");
      } else {
        const percents = await page.locator("li").getByText(/^\d+%$/).allTextContents();
        expect(percents).toHaveLength(3);
        const total = percents.reduce((sum, p) => sum + Number(p.replace("%", "")), 0);
        expect(total).toBe(100);
      }

      const isLast = n === 10;
      await page.getByRole("button", { name: isLast ? /see my results/i : /next question/i }).click();
    }
  });

  await test.step("the result: a profile, 8 scores, 10 reviewed questions", async () => {
    await expect(page).toHaveURL(/\/results\/[0-9a-f-]{36}$/, { timeout: 15_000 });
    await expect(page.getByText("Round complete")).toBeVisible();
    const title = await page.getByRole("heading", { level: 1 }).textContent();
    expect(title?.trim().length).toBeGreaterThan(0);
    await expect(page.getByRole("meter")).toHaveCount(8);
    await expect(page.getByText(/not a psychological or moral assessment/i)).toBeVisible();
    await expect(page.getByText(/^Question \d+ ·/)).toHaveCount(10);
  });

  await test.step("a finished round's game URL redirects to its result", async () => {
    await page.goto(roundUrl);
    await expect(page).toHaveURL(/\/results\//);
  });

  await test.step("the round shows up in history", async () => {
    await page.getByRole("link", { name: /history/i }).first().click();
    await expect(page).toHaveURL(/\/history$/);
    await expect(page.getByRole("heading", { name: /your rounds/i })).toBeVisible();
    await expect(page.getByRole("link").filter({ hasText: "Random" })).toHaveCount(1);
  });

  await test.step("logging out protects the app again", async () => {
    await page.getByRole("button", { name: /log out/i }).click();
    await expect(page).toHaveURL("/");
    await page.goto("/history");
    await expect(page).toHaveURL(/\/login\?next=%2Fhistory/);
  });
});

test("mobile: no horizontal scrolling through a question", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const player = uniquePlayer();

  await page.goto("/register");
  await page.getByLabel("Username").fill(player.username);
  await page.getByLabel("Email").fill(player.email);
  await page.getByLabel("Password").fill(player.password);
  await page.getByRole("button", { name: /create account/i }).click();
  await expect(page).toHaveURL(/\/play$/);

  await page.getByRole("button", { name: /^random/i }).click();
  await expect(page).toHaveURL(/\/play\/[0-9a-f-]{36}$/);
  await expect(page.getByText("What do you do?")).toBeVisible();

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  expect(overflow).toBe(false);
});

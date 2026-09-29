import { describe, expect, it } from "vitest";

import { safeNextPath } from "./navigation";

describe("safeNextPath", () => {
  it("falls back to /play when there is no next page", () => {
    expect(safeNextPath(null)).toBe("/play");
    expect(safeNextPath(undefined)).toBe("/play");
    expect(safeNextPath("")).toBe("/play");
  });

  it("keeps ordinary same-site paths", () => {
    expect(safeNextPath("/results/abc-123")).toBe("/results/abc-123");
    expect(safeNextPath("/history")).toBe("/history");
    expect(safeNextPath("/play?category=3")).toBe("/play?category=3");
  });

  // Each of these would send a freshly logged-in player to another website.
  it.each([
    "https://evil.example",
    "http://evil.example/play",
    "//evil.example",
    "/\\evil.example",
    "javascript:alert(1)",
    "evil.example",
    "play",
  ])("rejects %s", (next) => {
    expect(safeNextPath(next)).toBe("/play");
  });
});

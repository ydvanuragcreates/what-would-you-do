import { describe, expect, it } from "vitest";

import { labelForKey } from "./choices";

const press = (key: string, mods: Partial<{ ctrlKey: boolean; metaKey: boolean; altKey: boolean }> = {}) =>
  labelForKey({ key, ctrlKey: false, metaKey: false, altKey: false, ...mods });

describe("labelForKey", () => {
  it("maps letters and digits to options, in either case", () => {
    expect(press("a")).toBe("A");
    expect(press("A")).toBe("A");
    expect(press("1")).toBe("A");
    expect(press("b")).toBe("B");
    expect(press("2")).toBe("B");
    expect(press("c")).toBe("C");
    expect(press("3")).toBe("C");
  });

  it("ignores every other key", () => {
    for (const key of ["d", "4", "0", "Enter", " ", "Escape"]) {
      expect(press(key)).toBeUndefined();
    }
  });

  it("ignores browser shortcuts such as Ctrl+A (select all) and Cmd+C (copy)", () => {
    expect(press("a", { ctrlKey: true })).toBeUndefined();
    expect(press("c", { metaKey: true })).toBeUndefined();
    expect(press("b", { altKey: true })).toBeUndefined();
  });
});

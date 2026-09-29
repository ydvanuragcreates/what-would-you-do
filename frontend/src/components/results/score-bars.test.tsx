import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { DimensionScore } from "@/lib/api/types";

import { ScoreBars, formatScore } from "./score-bars";

const scores: DimensionScore[] = [
  { dimension: "honesty", label: "Honesty", score: 7.4 },
  { dimension: "self_interest", label: "Self-interest", score: 4.7 },
  { dimension: "empathy", label: "Empathy", score: null },
];

describe("formatScore", () => {
  it("always shows one decimal place", () => {
    expect(formatScore(8)).toBe("8.0");
    expect(formatScore(7.44)).toBe("7.4");
    expect(formatScore(0)).toBe("0.0");
  });
});

describe("ScoreBars", () => {
  it("shows real scores as 'x / 10'", () => {
    render(<ScoreBars scores={scores} />);

    const honesty = screen.getByTestId("score-honesty");
    expect(honesty).toHaveTextContent("7.4 / 10");
    expect(within(honesty).getByRole("meter")).toHaveAttribute("aria-valuenow", "7.4");
  });

  it("shows 'not enough data' instead of a fake number when the API sends null", () => {
    render(<ScoreBars scores={scores} />);

    const empathy = screen.getByTestId("score-empathy");
    expect(empathy).toHaveTextContent("Not enough data this round");
    expect(empathy).not.toHaveTextContent("/ 10");
    const meter = within(empathy).getByRole("meter");
    expect(meter).not.toHaveAttribute("aria-valuenow");
    expect(meter).toHaveAttribute("aria-valuetext", "Not enough data");
  });

  it("keeps the order the API gave", () => {
    render(<ScoreBars scores={scores} />);

    const labels = screen.getAllByRole("meter").map((meter) => meter.getAttribute("aria-label"));
    expect(labels).toEqual(["Honesty", "Self-interest", "Empathy"]);
  });
});

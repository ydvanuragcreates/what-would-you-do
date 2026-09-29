import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CROWD_AVAILABLE, CROWD_UNAVAILABLE, makeQuestion } from "@/test/fixtures";

import { CrowdBars } from "./crowd-bars";

const question = makeQuestion();

describe("CrowdBars", () => {
  it("shows each option's share of other players", () => {
    render(<CrowdBars choices={question.choices} crowd={CROWD_AVAILABLE} yourChoiceId={102} />);

    expect(within(screen.getByTestId("crowd-row-A")).getByText("67%")).toBeInTheDocument();
    expect(within(screen.getByTestId("crowd-row-B")).getByText("33%")).toBeInTheDocument();
    expect(within(screen.getByTestId("crowd-row-C")).getByText("0%")).toBeInTheDocument();
    expect(screen.getByText(/based on 3 other players/i)).toBeInTheDocument();
  });

  it("marks only the player's own choice with 'You'", () => {
    render(<CrowdBars choices={question.choices} crowd={CROWD_AVAILABLE} yourChoiceId={102} />);

    expect(within(screen.getByTestId("crowd-row-B")).getByText("You")).toBeInTheDocument();
    expect(within(screen.getByTestId("crowd-row-A")).queryByText("You")).not.toBeInTheDocument();
    expect(within(screen.getByTestId("crowd-row-C")).queryByText("You")).not.toBeInTheDocument();
  });

  it("says 'player' (not 'players') for a crowd of one", () => {
    const one = { ...CROWD_AVAILABLE, total_responses: 1 };

    render(<CrowdBars choices={question.choices} crowd={one} yourChoiceId={101} />);

    expect(screen.getByText(/based on 1 other player\./i)).toBeInTheDocument();
  });

  it("admits when there isn't enough data, and invents no percentages", () => {
    render(<CrowdBars choices={question.choices} crowd={CROWD_UNAVAILABLE} yourChoiceId={102} />);

    expect(screen.getByTestId("crowd-unavailable")).toHaveTextContent("Not enough responses yet.");
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
    // the options are still listed, and the player's own choice is still marked
    expect(screen.getByText("Keep it. That's their mistake.")).toBeInTheDocument();
    expect(within(screen.getByTestId("crowd-row-B")).getByText("You")).toBeInTheDocument();
  });
});

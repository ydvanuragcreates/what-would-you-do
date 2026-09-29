import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CROWD_AVAILABLE, CROWD_UNAVAILABLE, makeLastAnswer, makeQuestion } from "@/test/fixtures";

import { GameView, type GameViewProps } from "./game-view";

const question = makeQuestion();

function setup(overrides: Partial<GameViewProps> = {}) {
  const props: GameViewProps = {
    question,
    questionNumber: 4,
    totalQuestions: 10,
    pendingChoiceId: null,
    reveal: null,
    isLastQuestion: false,
    error: null,
    onChoose: vi.fn(),
    onNext: vi.fn(),
    ...overrides,
  };
  render(<GameView {...props} />);
  return { props, user: userEvent.setup() };
}

describe("GameView: answering", () => {
  it("shows the progress, the situation and all three options", () => {
    setup();

    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "4");
    expect(screen.getByText("Question 4")).toBeInTheDocument();
    expect(screen.getByText(question.situation_text)).toBeInTheDocument();
    expect(screen.getAllByRole("button")).toHaveLength(3);
    expect(screen.getByRole("button", { name: /option a: go back/i })).toBeInTheDocument();
  });

  it("chooses an option when it is clicked", async () => {
    const { props, user } = setup();

    await user.click(screen.getByRole("button", { name: /option b/i }));

    expect(props.onChoose).toHaveBeenCalledTimes(1);
    expect(props.onChoose).toHaveBeenCalledWith(question.choices[1]);
  });

  it.each([
    ["a", 0],
    ["B", 1],
    ["3", 2],
  ])("chooses an option when %s is pressed", async (key, index) => {
    const { props, user } = setup();

    await user.keyboard(key);

    expect(props.onChoose).toHaveBeenCalledWith(question.choices[index]);
  });

  it("ignores keys that aren't options, and browser shortcuts", async () => {
    const { props, user } = setup();

    await user.keyboard("d");
    await user.keyboard("{Control>}a{/Control}");
    await user.keyboard("{Enter}");

    expect(props.onChoose).not.toHaveBeenCalled();
    expect(props.onNext).not.toHaveBeenCalled();
  });

  it("locks every option while an answer is being sent, so it can't be double-submitted", async () => {
    const { props, user } = setup({ pendingChoiceId: 102 });

    for (const button of screen.getAllByRole("button")) expect(button).toBeDisabled();
    await user.keyboard("a");
    expect(props.onChoose).not.toHaveBeenCalled();
  });

  it("shows an error message", () => {
    setup({ error: "Can't reach the server." });

    expect(screen.getByRole("alert")).toHaveTextContent("Can't reach the server.");
  });
});

describe("GameView: reveal", () => {
  const reveal = makeLastAnswer(CROWD_AVAILABLE, 102);

  it("swaps the options for the crowd split, marking the player's choice", () => {
    setup({ reveal });

    expect(screen.getByText(/how everyone else answered/i)).toBeInTheDocument();
    expect(screen.getByText("67%")).toBeInTheDocument();
    expect(screen.getByTestId("crowd-row-B")).toHaveTextContent("You");
    expect(screen.queryByText(/what do you do/i)).not.toBeInTheDocument();
  });

  it("continues with the button or the Enter key", async () => {
    const { props, user } = setup({ reveal });

    await user.click(screen.getByRole("button", { name: /next question/i }));
    await user.keyboard("{Enter}");

    expect(props.onNext).toHaveBeenCalled();
  });

  it("does not accept a second answer during the reveal", async () => {
    const { props, user } = setup({ reveal });

    await user.keyboard("a");

    expect(props.onChoose).not.toHaveBeenCalled();
  });

  it("offers 'See my results' after the last question", () => {
    setup({ reveal, isLastQuestion: true, questionNumber: 10 });

    expect(screen.getByRole("button", { name: /see my results/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /next question/i })).not.toBeInTheDocument();
  });

  it("is honest when there isn't enough crowd data yet", () => {
    setup({ reveal: makeLastAnswer(CROWD_UNAVAILABLE, 101) });

    expect(screen.getByTestId("crowd-unavailable")).toHaveTextContent("Not enough responses yet.");
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });
});

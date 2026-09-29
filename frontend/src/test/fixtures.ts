import type { Choice, CrowdStats, LastAnswer, Question } from "@/lib/api/types";

/** A question shaped exactly like the API's ScenarioPublic. */
export function makeQuestion(overrides: Partial<Question> = {}): Question {
  const choices: Choice[] = [
    { id: 101, label: "A", text: "Go back and return it." },
    { id: 102, label: "B", text: "Keep it. That's their mistake." },
    { id: 103, label: "C", text: "Keep it, and give $20 to charity later." },
  ];
  return {
    id: 7,
    title: "Too Much Change",
    situation_text: "A cashier hands you $20 too much in change.",
    category: "money",
    choices,
    ...overrides,
  };
}

export const CROWD_AVAILABLE: CrowdStats = {
  available: true,
  total_responses: 3,
  message: null,
  choices: [
    { choice_id: 101, label: "A", percent: 67 },
    { choice_id: 102, label: "B", percent: 33 },
    { choice_id: 103, label: "C", percent: 0 },
  ],
};

export const CROWD_UNAVAILABLE: CrowdStats = {
  available: false,
  total_responses: null,
  message: "Not enough responses yet.",
  choices: [],
};

export function makeLastAnswer(crowd: CrowdStats, yourChoiceId = 102): LastAnswer {
  return { scenario_id: 7, your_choice_id: yourChoiceId, crowd };
}

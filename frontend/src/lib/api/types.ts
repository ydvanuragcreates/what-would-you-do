import type { components } from "./schema";

// Friendly names for the generated API types. Everything here mirrors the backend
// exactly (regenerate with `npm run gen:api`); nothing is redefined by hand.
type Schemas = components["schemas"];

export type User = Schemas["UserPublic"];
export type RoundState = Schemas["RoundStateResponse"];
export type Question = Schemas["ScenarioPublic"];
export type Choice = Schemas["ChoicePublic"];
export type ChoiceLabel = Choice["label"];
export type CrowdStats = Schemas["CrowdStats"];
export type LastAnswer = Schemas["LastAnswer"];
export type CategoriesResponse = Schemas["CategoriesResponse"];
export type CategoryOption = Schemas["CategoryPublic"];
export type RoundResult = Schemas["RoundResultResponse"];
export type QuestionReview = Schemas["QuestionReview"];
export type DimensionScore = Schemas["DimensionScore"];
export type ResultHistory = Schemas["ResultHistoryResponse"];
export type ResultSummary = Schemas["ResultSummary"];

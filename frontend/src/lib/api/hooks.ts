"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";
import { ApiError, call } from "./errors";
import type { RoundState, User } from "./types";

/** Every cache key in one place, so invalidation never depends on a typo. */
export const keys = {
  me: ["me"] as const,
  categories: ["categories"] as const,
  round: (roundId: string) => ["round", roundId] as const,
  result: (roundId: string) => ["result", roundId] as const,
  history: ["history"] as const,
};

// --- who am I? -------------------------------------------------------------------------

/** The logged-in user, or `null` when logged out. (A 401 is an answer, not a failure.) */
export function useCurrentUser() {
  return useQuery({
    queryKey: keys.me,
    queryFn: async (): Promise<User | null> => {
      try {
        return await call(api.GET("/api/v1/auth/me"));
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }
    },
    staleTime: 60_000,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { email: string; password: string }) =>
      call(api.POST("/api/v1/auth/login", { body })),
    onSuccess: (user) => queryClient.setQueryData(keys.me, user),
  });
}

export function useRegister() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { username: string; email: string; password: string }) =>
      call(api.POST("/api/v1/auth/register", { body })),
    onSuccess: (user) => queryClient.setQueryData(keys.me, user),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      // Logout returns 204 (no body), which `call` can't unwrap, so use the raw client.
      const { response } = await api.POST("/api/v1/auth/logout");
      if (!response.ok) throw new ApiError(response.status, "logout_failed", "Couldn't log out.");
    },
    // Drop everything cached: the next person on this device must not see any of it.
    onSuccess: () => queryClient.clear(),
  });
}

// --- playing ----------------------------------------------------------------------------

export function useCategories() {
  return useQuery({
    queryKey: keys.categories,
    queryFn: () => call(api.GET("/api/v1/scenarios/categories")),
  });
}

export function useStartRound() {
  return useMutation({
    mutationFn: (categoryId: number | null) =>
      call(api.POST("/api/v1/rounds", { body: { category_id: categoryId } })),
  });
}

export function useRound(roundId: string) {
  return useQuery({
    queryKey: keys.round(roundId),
    queryFn: () =>
      call(api.GET("/api/v1/rounds/{round_id}", { params: { path: { round_id: roundId } } })),
    // The server is the source of truth for progress; don't refetch on every focus.
    staleTime: Infinity,
  });
}

export function useSubmitAnswer(roundId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (answer: { scenarioId: number; choiceId: number }) =>
      call(
        api.POST("/api/v1/rounds/{round_id}/answers", {
          params: { path: { round_id: roundId } },
          body: { scenario_id: answer.scenarioId, choice_id: answer.choiceId },
        }),
      ),
    onSuccess: (state: RoundState) => {
      queryClient.setQueryData(keys.round(roundId), state);
      // A finished round adds to the history and produces a result.
      if (state.status === "completed") {
        void queryClient.invalidateQueries({ queryKey: keys.history });
      }
    },
  });
}

// --- results ----------------------------------------------------------------------------

export function useResult(roundId: string) {
  return useQuery({
    queryKey: keys.result(roundId),
    queryFn: () =>
      call(api.GET("/api/v1/results/{round_id}", { params: { path: { round_id: roundId } } })),
  });
}

export function useHistory() {
  return useQuery({
    queryKey: keys.history,
    queryFn: () => call(api.GET("/api/v1/users/me/results", { params: { query: { limit: 50 } } })),
  });
}

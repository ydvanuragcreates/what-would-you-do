/** One field-level problem from the API's 422 responses. */
export type FieldProblem = { field: string; message: string };

/**
 * Every failed API call becomes one of these, so screens handle a single error shape.
 * `code` is the backend's machine-readable code (e.g. "invalid_credentials").
 */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly details: FieldProblem[] = [],
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type ErrorBody = {
  error?: {
    code?: string;
    message?: string;
    details?: { field: string; message: string }[] | null;
  };
};

export function toApiError(status: number, body: unknown): ApiError {
  const error = (body as ErrorBody | undefined)?.error;
  return new ApiError(
    status,
    error?.code ?? "unknown_error",
    error?.message ?? "Something went wrong. Please try again.",
    error?.details ?? [],
  );
}

export const NETWORK_ERROR_MESSAGE = "Can't reach the server. Check your connection and try again.";

/**
 * Unwrap an openapi-fetch result: return the data, or throw an ApiError.
 * A network failure (server down, offline) is also an ApiError, with status 0.
 */
export async function call<T>(
  request: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  let result;
  try {
    result = await request;
  } catch {
    throw new ApiError(0, "network_error", NETWORK_ERROR_MESSAGE);
  }
  if (result.error !== undefined || result.data === undefined) {
    throw toApiError(result.response.status, result.error);
  }
  return result.data;
}

export function isApiError(error: unknown, code?: string): error is ApiError {
  return error instanceof ApiError && (code === undefined || error.code === code);
}

/** Text safe to show a player for any thrown error. */
export function messageFor(error: unknown): string {
  return error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
}

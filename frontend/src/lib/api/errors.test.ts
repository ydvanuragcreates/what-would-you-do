import { describe, expect, it } from "vitest";

import { ApiError, NETWORK_ERROR_MESSAGE, call, messageFor, toApiError } from "./errors";

const respond = (status: number) => new Response(null, { status });

describe("toApiError", () => {
  it("reads the backend's error envelope", () => {
    const error = toApiError(409, {
      error: { code: "account_exists", message: "That username or email is already registered." },
    });

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(409);
    expect(error.code).toBe("account_exists");
    expect(error.message).toBe("That username or email is already registered.");
  });

  it("keeps field-level details from validation errors", () => {
    const error = toApiError(422, {
      error: {
        code: "validation_error",
        message: "Some fields are invalid.",
        details: [{ field: "password", message: "Password must be between 8 and 128 characters." }],
      },
    });

    expect(error.details).toEqual([
      { field: "password", message: "Password must be between 8 and 128 characters." },
    ]);
  });

  it("copes with a body that isn't our envelope (proxy error pages, empty bodies)", () => {
    for (const body of [undefined, null, "Bad Gateway", { detail: "x" }]) {
      const error = toApiError(502, body);
      expect(error.code).toBe("unknown_error");
      expect(error.message).toMatch(/something went wrong/i);
    }
  });
});

describe("call", () => {
  it("returns the data on success", async () => {
    await expect(call(Promise.resolve({ data: { ok: 1 }, response: respond(200) }))).resolves.toEqual({
      ok: 1,
    });
  });

  it("throws an ApiError carrying the status and code on failure", async () => {
    const failure = call(
      Promise.resolve({
        error: { error: { code: "invalid_credentials", message: "Invalid email or password." } },
        response: respond(401),
      }),
    );

    await expect(failure).rejects.toMatchObject({ status: 401, code: "invalid_credentials" });
  });

  it("turns a network failure into a friendly ApiError with status 0", async () => {
    const failure = call(Promise.reject(new TypeError("fetch failed")));

    await expect(failure).rejects.toMatchObject({
      status: 0,
      code: "network_error",
      message: NETWORK_ERROR_MESSAGE,
    });
  });
});

describe("messageFor", () => {
  it("shows an API error's own message but never leaks other errors' internals", () => {
    expect(messageFor(new ApiError(401, "x", "Invalid email or password."))).toBe(
      "Invalid email or password.",
    );
    expect(messageFor(new Error("TypeError: cannot read properties of undefined"))).toBe(
      "Something went wrong. Please try again.",
    );
  });
});

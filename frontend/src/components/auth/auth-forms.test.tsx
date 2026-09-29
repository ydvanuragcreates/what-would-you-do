/**
 * Login and register forms, with the API hooks faked.
 *
 * Regression guard: after a successful login/sign-up the page must do a FULL reload.
 * A client-side transition replays Next.js's cached redirect to /login (from a prefetch
 * made while logged out) and bounces the player straight back. See lib/navigation.ts.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/errors";

let search = "";
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(search),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

const fullReload = vi.fn();
vi.mock("@/lib/navigation", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/navigation")>()),
  navigateWithFullReload: (path: string) => fullReload(path),
}));

const loginMutate = vi.fn();
const registerMutate = vi.fn();
vi.mock("@/lib/api/hooks", () => ({
  useLogin: () => ({ mutate: loginMutate, isPending: false }),
  useRegister: () => ({ mutate: registerMutate, isPending: false }),
}));

import { LoginForm } from "./login-form";
import { RegisterForm } from "./register-form";

type Callbacks = { onSuccess: () => void; onError: (error: unknown) => void };
const lastCallbacks = (mutate: typeof loginMutate) => mutate.mock.calls.at(-1)![1] as Callbacks;

beforeEach(() => {
  vi.clearAllMocks();
  search = "";
});

describe("LoginForm", () => {
  async function submit(email = "anna@example.com", password = "a long password") {
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Email"), email);
    await user.type(screen.getByLabelText("Password"), password);
    await user.click(screen.getByRole("button", { name: /^log in$/i }));
    return user;
  }

  it("asks for both fields before contacting the server", async () => {
    render(<LoginForm />);

    await userEvent.setup().click(screen.getByRole("button", { name: /^log in$/i }));

    expect(await screen.findByText("Enter your email")).toBeInTheDocument();
    expect(screen.getByText("Enter your password")).toBeInTheDocument();
    expect(loginMutate).not.toHaveBeenCalled();
  });

  it("sends the credentials", async () => {
    render(<LoginForm />);

    await submit();

    await waitFor(() => expect(loginMutate).toHaveBeenCalledTimes(1));
    expect(loginMutate.mock.calls[0][0]).toEqual({
      email: "anna@example.com",
      password: "a long password",
    });
  });

  it("does a full page reload to /play after logging in", async () => {
    render(<LoginForm />);
    await submit();
    await waitFor(() => expect(loginMutate).toHaveBeenCalled());

    lastCallbacks(loginMutate).onSuccess();

    expect(fullReload).toHaveBeenCalledWith("/play");
  });

  it("returns to the page the player was heading for", async () => {
    search = "next=%2Fresults%2Fabc";
    render(<LoginForm />);
    await submit();
    await waitFor(() => expect(loginMutate).toHaveBeenCalled());

    lastCallbacks(loginMutate).onSuccess();

    expect(fullReload).toHaveBeenCalledWith("/results/abc");
  });

  it("never redirects to another website, whatever ?next= says", async () => {
    search = "next=https%3A%2F%2Fevil.example";
    render(<LoginForm />);
    await submit();
    await waitFor(() => expect(loginMutate).toHaveBeenCalled());

    lastCallbacks(loginMutate).onSuccess();

    expect(fullReload).toHaveBeenCalledWith("/play");
  });

  it("shows the server's message for a wrong password", async () => {
    render(<LoginForm />);
    await submit();
    await waitFor(() => expect(loginMutate).toHaveBeenCalled());

    lastCallbacks(loginMutate).onError(
      new ApiError(401, "invalid_credentials", "Invalid email or password."),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password.");
    expect(fullReload).not.toHaveBeenCalled();
  });
});

describe("RegisterForm", () => {
  async function fillAndSubmit(values = { username: "anna_k", email: "anna@example.com", password: "a long password" }) {
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Username"), values.username);
    await user.type(screen.getByLabelText("Email"), values.email);
    await user.type(screen.getByLabelText("Password"), values.password);
    await user.click(screen.getByRole("button", { name: /create account/i }));
  }

  it("checks username, email and password before contacting the server", async () => {
    render(<RegisterForm />);

    await fillAndSubmit({ username: "a b", email: "nope", password: "short" });

    expect(await screen.findByText("Letters, numbers and underscores only")).toBeInTheDocument();
    expect(screen.getByText("Enter a valid email address")).toBeInTheDocument();
    expect(screen.getByText("At least 8 characters", { selector: "p[role=alert]" })).toBeInTheDocument();
    expect(registerMutate).not.toHaveBeenCalled();
  });

  it("does a full page reload after signing up", async () => {
    render(<RegisterForm />);
    await fillAndSubmit();
    await waitFor(() => expect(registerMutate).toHaveBeenCalledTimes(1));

    lastCallbacks(registerMutate).onSuccess();

    expect(fullReload).toHaveBeenCalledWith("/play");
  });

  it("explains a taken username or email", async () => {
    render(<RegisterForm />);
    await fillAndSubmit();
    await waitFor(() => expect(registerMutate).toHaveBeenCalled());

    lastCallbacks(registerMutate).onError(
      new ApiError(409, "account_exists", "That username or email is already registered."),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("already registered");
  });

  it("shows a field-level server rejection next to that field", async () => {
    render(<RegisterForm />);
    await fillAndSubmit();
    await waitFor(() => expect(registerMutate).toHaveBeenCalled());

    lastCallbacks(registerMutate).onError(
      new ApiError(422, "validation_error", "Some fields are invalid.", [
        { field: "username", message: "That username isn't allowed." },
      ]),
    );

    expect(await screen.findByText("That username isn't allowed.")).toBeInTheDocument();
  });
});

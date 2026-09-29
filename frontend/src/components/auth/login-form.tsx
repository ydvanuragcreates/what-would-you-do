"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { FormField } from "@/components/auth/form-field";
import { Button } from "@/components/ui/button";
import { useLogin } from "@/lib/api/hooks";
import { messageFor } from "@/lib/api/errors";
import { navigateWithFullReload, safeNextPath } from "@/lib/navigation";
import { type LoginValues, loginSchema } from "@/lib/validation";

export function LoginForm() {
  const next = safeNextPath(useSearchParams().get("next"));
  const login = useLogin();
  const [formError, setFormError] = useState<string | null>(null);
  const [redirecting, setRedirecting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) });

  const onSubmit = handleSubmit((values) => {
    setFormError(null);
    login.mutate(values, {
      onSuccess: () => {
        setRedirecting(true); // keep the button disabled until the page actually changes
        navigateWithFullReload(next);
      },
      // 401 (wrong details), 429 (too many tries), network problems: the API's own
      // wording is already player-friendly.
      onError: (error) => setFormError(messageFor(error)),
    });
  });

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-5">
      <FormField
        id="email"
        label="Email"
        type="email"
        autoComplete="email"
        placeholder="you@example.com"
        error={errors.email}
        registration={register("email")}
      />
      <FormField
        id="password"
        label="Password"
        type="password"
        autoComplete="current-password"
        error={errors.password}
        registration={register("password")}
      />

      {formError && (
        <p role="alert" className="bg-destructive/10 text-destructive rounded-lg px-3 py-2 text-sm">
          {formError}
        </p>
      )}

      <Button type="submit" size="xl" className="w-full" disabled={login.isPending || redirecting}>
        {login.isPending || redirecting ? "Logging in…" : "Log in"}
      </Button>

      <p className="text-muted-foreground text-center text-sm">
        New here?{" "}
        <Link
          href={next === "/play" ? "/register" : `/register?next=${encodeURIComponent(next)}`}
          className="text-foreground underline underline-offset-4"
        >
          Create an account
        </Link>
      </p>
    </form>
  );
}

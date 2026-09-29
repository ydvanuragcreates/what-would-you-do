"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { FormField } from "@/components/auth/form-field";
import { Button } from "@/components/ui/button";
import { useRegister } from "@/lib/api/hooks";
import { ApiError, messageFor } from "@/lib/api/errors";
import { navigateWithFullReload, safeNextPath } from "@/lib/navigation";
import { type RegisterValues, registerSchema } from "@/lib/validation";

export function RegisterForm() {
  const next = safeNextPath(useSearchParams().get("next"));
  const registerUser = useRegister();
  const [formError, setFormError] = useState<string | null>(null);
  const [redirecting, setRedirecting] = useState(false);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) });

  const onSubmit = handleSubmit((values) => {
    setFormError(null);
    registerUser.mutate(values, {
      // Registering also logs you in, so go straight to where you were headed.
      onSuccess: () => {
        setRedirecting(true); // keep the button disabled until the page actually changes
        navigateWithFullReload(next);
      },
      onError: (error) => {
        // The server disagreed with a specific field: show it next to that field.
        if (error instanceof ApiError && error.status === 422 && error.details.length > 0) {
          for (const { field, message } of error.details) {
            if (field === "username" || field === "email" || field === "password") {
              setError(field, { message });
            }
          }
          return;
        }
        setFormError(messageFor(error));
      },
    });
  });

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-5">
      <FormField
        id="username"
        label="Username"
        autoComplete="username"
        placeholder="anna_k"
        hint="3–30 letters, numbers or underscores"
        error={errors.username}
        registration={register("username")}
      />
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
        autoComplete="new-password"
        hint="At least 8 characters"
        error={errors.password}
        registration={register("password")}
      />

      {formError && (
        <p role="alert" className="bg-destructive/10 text-destructive rounded-lg px-3 py-2 text-sm">
          {formError}
        </p>
      )}

      <Button
        type="submit"
        size="xl"
        className="w-full"
        disabled={registerUser.isPending || redirecting}
      >
        {registerUser.isPending || redirecting ? "Creating account…" : "Create account"}
      </Button>

      <p className="text-muted-foreground text-center text-sm">
        Already have an account?{" "}
        <Link
          href={next === "/play" ? "/login" : `/login?next=${encodeURIComponent(next)}`}
          className="text-foreground underline underline-offset-4"
        >
          Log in
        </Link>
      </p>
    </form>
  );
}

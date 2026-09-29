import type { Metadata } from "next";
import { Suspense } from "react";

import { RegisterForm } from "@/components/auth/register-form";

export const metadata: Metadata = { title: "Sign up" };

export default function RegisterPage() {
  return (
    <>
      <h1 className="mb-1 text-2xl font-semibold">Create your account</h1>
      <p className="text-muted-foreground mb-6 text-sm">
        It takes a minute, then you can play right away.
      </p>
      <Suspense>
        <RegisterForm />
      </Suspense>
    </>
  );
}

import type { Metadata } from "next";
import { Suspense } from "react";

import { LoginForm } from "@/components/auth/login-form";

export const metadata: Metadata = { title: "Log in" };

export default function LoginPage() {
  return (
    <>
      <h1 className="mb-1 text-2xl font-semibold">Welcome back</h1>
      <p className="text-muted-foreground mb-6 text-sm">Log in to start a round.</p>
      {/* useSearchParams (for ?next=) needs a Suspense boundary in this Next.js version. */}
      <Suspense>
        <LoginForm />
      </Suspense>
    </>
  );
}

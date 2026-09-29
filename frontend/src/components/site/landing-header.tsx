"use client";

import Link from "next/link";

import { Logo } from "@/components/site/logo";
import { buttonVariants } from "@/components/ui/button";
import { useCurrentUser } from "@/lib/api/hooks";
import { cn } from "@/lib/utils";

export function LandingHeader() {
  const { data: user } = useCurrentUser();

  return (
    <header className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
      <Logo />
      <nav aria-label="Main" className="flex items-center gap-2">
        {user ? (
          <Link href="/play" className={cn(buttonVariants({ size: "lg" }), "px-4")}>
            Play
          </Link>
        ) : (
          <>
            <Link href="/login" className={cn(buttonVariants({ variant: "ghost", size: "lg" }), "px-3")}>
              Log in
            </Link>
            <Link href="/register" className={cn(buttonVariants({ variant: "outline", size: "lg" }), "px-3")}>
              Sign up
            </Link>
          </>
        )}
      </nav>
    </header>
  );
}

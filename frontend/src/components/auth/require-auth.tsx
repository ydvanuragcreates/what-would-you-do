"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { ErrorState, PageLoading } from "@/components/states";
import { useCurrentUser } from "@/lib/api/hooks";
import { messageFor } from "@/lib/api/errors";

/**
 * Wrap any screen that needs a logged-in player. proxy.ts already turns away people
 * with no cookie; this also handles an expired or invalid login (cookie present, but
 * the backend says 401) by sending them to /login and back afterwards.
 */
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { data: user, isPending, error, refetch } = useCurrentUser();

  useEffect(() => {
    if (user === null) router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [user, pathname, router]);

  if (isPending || user === null) return <PageLoading label="Checking your login…" />;
  if (error) return <ErrorState message={messageFor(error)} onRetry={() => void refetch()} />;
  return <>{children}</>;
}

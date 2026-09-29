"use client";

import { LogOut } from "lucide-react";
import Link from "next/link";

import { Logo } from "@/components/site/logo";
import { Button } from "@/components/ui/button";
import { useCurrentUser, useLogout } from "@/lib/api/hooks";
import { navigateWithFullReload } from "@/lib/navigation";

export function AppHeader() {
  const { data: user } = useCurrentUser();
  const logout = useLogout();

  return (
    <header className="border-border/60 border-b">
      <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between gap-4 px-4 sm:px-6">
        <Logo />
        <nav aria-label="Main" className="flex items-center gap-1 text-sm sm:gap-2">
          <Link href="/play" className="text-muted-foreground hover:text-foreground rounded-md px-2 py-1.5 transition-colors">
            Play
          </Link>
          <Link href="/history" className="text-muted-foreground hover:text-foreground rounded-md px-2 py-1.5 transition-colors">
            History
          </Link>
          {user && (
            <span className="text-muted-foreground hidden max-w-32 truncate px-2 sm:inline" title={user.username}>
              {user.username}
            </span>
          )}
          <Button
            variant="ghost"
            size="sm"
            disabled={logout.isPending}
            // Full reload: the login state changed, so nothing cached may be reused.
            onClick={() => logout.mutate(undefined, { onSuccess: () => navigateWithFullReload("/") })}
          >
            <LogOut aria-hidden /> Log out
          </Button>
        </nav>
      </div>
    </header>
  );
}

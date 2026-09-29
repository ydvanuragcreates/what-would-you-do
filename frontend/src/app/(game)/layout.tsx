import { RequireAuth } from "@/components/auth/require-auth";
import { LeaveRoundLink } from "@/components/game/game-screen";
import { Logo } from "@/components/site/logo";

// The game screen is deliberately chrome-free: just a slim bar, so the question is the focus.
export default function GameLayout({ children }: LayoutProps<"/">) {
  return (
    <RequireAuth>
      <header className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between px-4 sm:px-6">
        <Logo className="text-sm" />
        <LeaveRoundLink />
      </header>
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 pt-4 pb-16 sm:px-6">{children}</main>
    </RequireAuth>
  );
}

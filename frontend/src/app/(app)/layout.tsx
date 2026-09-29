import { RequireAuth } from "@/components/auth/require-auth";
import { AppHeader } from "@/components/site/app-header";

export default function AppLayout({ children }: LayoutProps<"/">) {
  return (
    <RequireAuth>
      <AppHeader />
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6 sm:py-12">{children}</main>
    </RequireAuth>
  );
}

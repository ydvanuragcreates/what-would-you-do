import { Logo } from "@/components/site/logo";

export default function AuthLayout({ children }: LayoutProps<"/">) {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-4 py-10">
      <Logo className="mb-8 text-lg" />
      <div className="surface w-full max-w-md p-6 sm:p-8">{children}</div>
    </main>
  );
}

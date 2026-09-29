import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-5 px-4 py-24 text-center">
      <p className="text-gradient font-heading text-7xl font-bold">404</p>
      <h1 className="text-2xl font-semibold">There&apos;s nothing here</h1>
      <p className="text-muted-foreground">That page doesn&apos;t exist.</p>
      <Link href="/" className={buttonVariants({ size: "lg" })}>
        Back to the start
      </Link>
    </main>
  );
}

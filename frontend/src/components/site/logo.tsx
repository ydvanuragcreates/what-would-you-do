import Link from "next/link";

import { cn } from "@/lib/utils";

export function Logo({ className }: { className?: string }) {
  return (
    <Link
      href="/"
      className={cn(
        "font-heading inline-flex items-center gap-2 text-base font-semibold tracking-tight",
        className,
      )}
    >
      <span
        aria-hidden
        className="grid size-7 place-items-center rounded-lg bg-gradient-to-br from-violet-400 to-amber-300 text-sm font-bold text-[#140f24]"
      >
        ?
      </span>
      <span>
        What Would <span className="text-gradient">You</span> Do?
      </span>
    </Link>
  );
}

import type { Metadata } from "next";

import { CategoryPicker } from "@/components/play/category-picker";

export const metadata: Metadata = { title: "Choose your round" };

export default function PlayPage() {
  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold sm:text-5xl">Choose your round</h1>
        <p className="text-muted-foreground text-lg">
          Pick a theme, or let fate decide. Every round is ten situations.
        </p>
      </div>
      <CategoryPicker />
    </div>
  );
}

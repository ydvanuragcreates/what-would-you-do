import type { Metadata } from "next";

import { HistoryList } from "@/components/history/history-list";

export const metadata: Metadata = { title: "Your rounds" };

export default function HistoryPage() {
  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold sm:text-5xl">Your rounds</h1>
        <p className="text-muted-foreground text-lg">Everything you&apos;ve finished, newest first.</p>
      </div>
      <HistoryList />
    </div>
  );
}

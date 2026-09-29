import type { Metadata } from "next";

import { ResultsScreen } from "@/components/results/results-screen";

export const metadata: Metadata = { title: "Your result" };

export default async function ResultsPage({ params }: { params: Promise<{ roundId: string }> }) {
  const { roundId } = await params;
  return <ResultsScreen roundId={roundId} />;
}

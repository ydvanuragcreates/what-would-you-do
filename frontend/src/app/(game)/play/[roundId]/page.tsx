import type { Metadata } from "next";

import { GameScreen } from "@/components/game/game-screen";

export const metadata: Metadata = { title: "Playing" };

// In this Next.js version `params` is a Promise.
export default async function RoundPage({ params }: { params: Promise<{ roundId: string }> }) {
  const { roundId } = await params;
  return <GameScreen roundId={roundId} />;
}

import { ArrowRight, Eye, MessagesSquare, Sparkles } from "lucide-react";
import Link from "next/link";

import { Disclaimer } from "@/components/site/disclaimer";
import { LandingHeader } from "@/components/site/landing-header";
import { Logo } from "@/components/site/logo";
import { buttonVariants } from "@/components/ui/button";
import { CHOICE_STYLES } from "@/lib/choices";
import { cn } from "@/lib/utils";

const SAMPLE = {
  situation:
    "A cashier hands you $20 too much in change. You notice at the door. The shop is packed and nobody saw.",
  choices: [
    { label: "A", text: "Go back and return it." },
    { label: "B", text: "Keep it. That's their mistake." },
    { label: "C", text: "Keep it, and give $20 to charity later." },
  ] as const,
};

const STEPS = [
  {
    icon: Eye,
    title: "Read the situation",
    text: "Short, realistic moments: a friend asks a favour, a colleague slips up, temptation shows up.",
  },
  {
    icon: MessagesSquare,
    title: "Pick what you'd do",
    text: "Three options, none of them obviously right. Every choice costs you something.",
  },
  {
    icon: Sparkles,
    title: "See where you land",
    text: "Find out what everyone else chose, then get a playful read on how your round leaned.",
  },
];

const DIMENSIONS = [
  "Honesty",
  "Loyalty",
  "Empathy",
  "Self-interest",
  "Risk",
  "Responsibility",
  "Fairness",
  "Social pressure",
];

export default function LandingPage() {
  return (
    <>
      <LandingHeader />

      <main className="flex-1">
        {/* Hero */}
        <section className="mx-auto grid w-full max-w-6xl items-center gap-12 px-4 pt-10 pb-20 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:gap-16 lg:pt-20 lg:pb-28">
          <div className="animate-in fade-in slide-in-from-bottom-4 space-y-7 duration-700">
            <p className="border-border bg-card/60 text-muted-foreground inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium backdrop-blur-sm">
              <span className="bg-choice-b size-1.5 rounded-full" aria-hidden />
              An interactive morality game · about 5 minutes
            </p>
            <h1 className="text-5xl leading-[1.03] font-bold sm:text-6xl lg:text-7xl">
              What would <span className="text-gradient">YOU</span> do?
            </h1>
            <p className="text-muted-foreground max-w-xl text-lg leading-relaxed sm:text-xl">
              Ten tricky situations. Three honest options each. No right answers. Make your call, see
              what everyone else picked, then discover the pattern in your choices.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <Link
                href="/play" prefetch={false}
                className={cn(buttonVariants({ size: "xl" }), "group")}
              >
                Start a Round
                <ArrowRight className="transition-transform group-hover:translate-x-0.5" aria-hidden />
              </Link>
              <a href="#how-it-works" className={cn(buttonVariants({ variant: "ghost", size: "xl" }))}>
                How it works
              </a>
            </div>
            <p className="text-muted-foreground text-sm">Free to play · takes a minute to sign up</p>
          </div>

          {/* A real scenario from the game. No percentages: those must come from real players. */}
          <div
            className="animate-in fade-in slide-in-from-bottom-6 delay-150 duration-700"
            aria-label="Example question"
          >
            <div className="surface relative p-6 shadow-[0_0_80px_-20px_var(--glow)] sm:p-8">
              <div className="text-muted-foreground mb-5 flex items-center justify-between text-xs font-medium tracking-widest uppercase">
                <span>Round 01</span>
                <span>Question 4 / 10</span>
              </div>
              <p className="font-heading text-xl leading-snug font-medium sm:text-2xl">
                {SAMPLE.situation}
              </p>
              <p className="text-muted-foreground mt-5 mb-3 text-sm">What do you do?</p>
              <ul className="space-y-2.5">
                {SAMPLE.choices.map((choice) => (
                  <li
                    key={choice.label}
                    className="border-border bg-background/40 flex items-center gap-3 rounded-xl border px-3.5 py-3"
                  >
                    <span
                      className={cn(
                        "grid size-7 shrink-0 place-items-center rounded-lg text-sm font-bold",
                        CHOICE_STYLES[choice.label].badge,
                      )}
                      aria-hidden
                    >
                      {choice.label}
                    </span>
                    <span className="text-[0.95rem]">{choice.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section id="how-it-works" className="mx-auto w-full max-w-6xl scroll-mt-8 px-4 pb-20 sm:px-6">
          <h2 className="mb-8 text-center text-3xl font-semibold sm:text-4xl">How it works</h2>
          <ol className="grid gap-4 md:grid-cols-3">
            {STEPS.map((step, index) => (
              <li key={step.title} className="surface p-6">
                <div className="mb-4 flex items-center gap-3">
                  <span className="bg-primary/15 text-primary grid size-10 place-items-center rounded-xl">
                    <step.icon className="size-5" aria-hidden />
                  </span>
                  <span className="text-muted-foreground font-mono text-sm">0{index + 1}</span>
                </div>
                <h3 className="mb-1.5 text-lg font-semibold">{step.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{step.text}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* What the result looks like */}
        <section className="mx-auto w-full max-w-4xl px-4 pb-24 text-center sm:px-6">
          <h2 className="mb-3 text-3xl font-semibold sm:text-4xl">Your round, in eight dimensions</h2>
          <p className="text-muted-foreground mx-auto mb-7 max-w-2xl">
            At the end you get a playful profile of how your choices leaned this time.
          </p>
          <ul className="mb-10 flex flex-wrap justify-center gap-2">
            {DIMENSIONS.map((name) => (
              <li
                key={name}
                className="border-border bg-card/60 rounded-full border px-4 py-1.5 text-sm backdrop-blur-sm"
              >
                {name}
              </li>
            ))}
          </ul>
          <Link href="/play" prefetch={false} className={cn(buttonVariants({ size: "xl" }))}>
            Start a Round <ArrowRight aria-hidden />
          </Link>
        </section>
      </main>

      <footer className="border-border/60 border-t">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-3 px-4 py-8 sm:px-6 md:flex-row md:items-center md:justify-between">
          <Logo className="text-sm" />
          <Disclaimer className="max-w-xl md:text-right" text="For entertainment and self-reflection only. This is not a scientifically validated psychological or morality assessment, and your results don't say anything definitive about who you are." />
        </div>
      </footer>
    </>
  );
}

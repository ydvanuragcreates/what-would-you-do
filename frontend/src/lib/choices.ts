import type { ChoiceLabel } from "@/lib/api/types";

/** Keyboard keys that select each option, on top of clicking. */
export const KEYS_FOR_LABEL: Record<ChoiceLabel, string[]> = {
  A: ["a", "1"],
  B: ["b", "2"],
  C: ["c", "3"],
};

/**
 * Tailwind classes per option. Written out in full (not built from strings) so
 * Tailwind's scanner can see every class and keep it in the build.
 */
export const CHOICE_STYLES: Record<
  ChoiceLabel,
  { badge: string; bar: string; ring: string; text: string }
> = {
  A: {
    badge: "bg-choice-a text-background",
    bar: "bg-choice-a",
    ring: "border-choice-a/70 bg-choice-a/10",
    text: "text-choice-a",
  },
  B: {
    badge: "bg-choice-b text-background",
    bar: "bg-choice-b",
    ring: "border-choice-b/70 bg-choice-b/10",
    text: "text-choice-b",
  },
  C: {
    badge: "bg-choice-c text-background",
    bar: "bg-choice-c",
    ring: "border-choice-c/70 bg-choice-c/10",
    text: "text-choice-c",
  },
};

/** The option a pressed key stands for, or undefined. Ignores keys used with Ctrl/Alt/Meta. */
export function labelForKey(event: {
  key: string;
  ctrlKey: boolean;
  metaKey: boolean;
  altKey: boolean;
}): ChoiceLabel | undefined {
  if (event.ctrlKey || event.metaKey || event.altKey) return undefined;
  const key = event.key.toLowerCase();
  return (Object.keys(KEYS_FOR_LABEL) as ChoiceLabel[]).find((label) =>
    KEYS_FOR_LABEL[label].includes(key),
  );
}

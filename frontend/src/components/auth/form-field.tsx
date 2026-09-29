import type { FieldError, UseFormRegisterReturn } from "react-hook-form";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Props = {
  id: string;
  label: string;
  type?: string;
  autoComplete?: string;
  placeholder?: string;
  hint?: string;
  error?: FieldError;
  registration: UseFormRegisterReturn;
};

/** A labelled input whose error message is announced by screen readers. */
export function FormField({ id, label, type = "text", autoComplete, placeholder, hint, error, registration }: Props) {
  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined;
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        type={type}
        autoComplete={autoComplete}
        placeholder={placeholder}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className="h-11 text-base"
        {...registration}
      />
      {error ? (
        <p id={`${id}-error`} role="alert" className="text-destructive text-sm">
          {error.message}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="text-muted-foreground text-sm">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

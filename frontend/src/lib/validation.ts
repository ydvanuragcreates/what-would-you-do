import { z } from "zod";

// These mirror the backend's rules (backend/app/schemas/auth.py) so people get instant
// feedback. The backend re-checks everything: this is convenience, not security.

export const loginSchema = z.object({
  email: z.string().trim().min(1, "Enter your email"),
  password: z.string().min(1, "Enter your password"),
});

export const registerSchema = z.object({
  username: z
    .string()
    .trim()
    .min(3, "At least 3 characters")
    .max(30, "At most 30 characters")
    .regex(/^[A-Za-z0-9_]+$/, "Letters, numbers and underscores only"),
  email: z.email("Enter a valid email address"),
  password: z.string().min(8, "At least 8 characters").max(128, "At most 128 characters"),
});

export type LoginValues = z.infer<typeof loginSchema>;
export type RegisterValues = z.infer<typeof registerSchema>;

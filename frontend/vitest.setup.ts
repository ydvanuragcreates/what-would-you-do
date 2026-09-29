import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Unmount whatever a test rendered, so tests can't affect each other.
afterEach(() => cleanup());

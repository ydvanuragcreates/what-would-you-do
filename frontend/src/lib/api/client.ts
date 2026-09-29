import createClient from "openapi-fetch";

import type { paths } from "./schema";

/**
 * The typed API client. Paths, request bodies and responses all come from the
 * backend's OpenAPI schema (`npm run gen:api`), so a mistake here is a compile error.
 *
 * `baseUrl` is empty on purpose: requests go to THIS site's /api/*, which Next.js
 * proxies to the backend (see next.config.ts). The login cookie therefore stays
 * first-party and is sent automatically.
 */
export const api = createClient<paths>({ baseUrl: "", credentials: "same-origin" });

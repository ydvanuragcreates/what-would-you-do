import type { NextConfig } from "next";

// Where the FastAPI backend lives. The browser never talks to it directly: it calls
// /api/* on THIS site and Next.js forwards the request. That keeps the login cookie
// first-party (works in every browser, including Safari) and makes CORS a non-issue.
//
// NOTE: rewrite destinations are baked in at BUILD time, so BACKEND_URL must be set
// when you run `npm run build`, not just when you run `npm start`.
const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8010";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backendUrl}/api/:path*` }];
  },
};

export default nextConfig;

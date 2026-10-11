import type { NextConfig } from "next";

declare const process: { env: { API_URL?: string; VERCEL?: string } };

const nextConfig: NextConfig = {
  async rewrites() {
    // Local dev talks to the local API. On Vercel, fall back to the hosted synthetic-only demo API when
    // API_URL is not set, so preview deployments work without extra project settings.
    const hosted = "https://d1-diagnostic-odyssey-api.vercel.app";
    const api = process.env.API_URL ?? (process.env.VERCEL ? hosted : "http://127.0.0.1:8000");
    return [{ source: "/api/:path*", destination: `${api}/:path*` }];
  },
};

export default nextConfig;

import type { NextConfig } from "next";

declare const process: { env: { API_URL?: string } };

const nextConfig: NextConfig = {
  async rewrites() {
    const api = process.env.API_URL ?? "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: `${api}/:path*` }];
  },
};

export default nextConfig;

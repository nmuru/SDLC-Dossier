import type { NextConfig } from "next";

const Production_mode = true;

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: Production_mode
      ? "http://34.205.18.52:8000"
      : "http://localhost:8000",
  },
};

export default nextConfig;
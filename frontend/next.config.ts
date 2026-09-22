import type { NextConfig } from "next";

const Production_mode = true;

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: Production_mode
      ? "https://3.91.148.139"
      : "http://localhost:8000",
  },
};

export default nextConfig;

import type { NextConfig } from "next";

const Production_mode = true;

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: Production_mode
      ? "https://sdlc-dossier-api.onrender.com"
      : "http://localhost:8000",
  },
};

export default nextConfig;

const Production_mode = true;

const nextConfig:
 NextConfig = {
  allowedDevOrigins: ['3.87.44.100'],
  env: {
    NEXT_PUBLIC_API_URL: "http://3.87.44.100:8000",
  },
};

export default nextConfig;
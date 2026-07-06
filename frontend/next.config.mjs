/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: [],
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    NEXT_PUBLIC_AI_AGENT_URL: process.env.NEXT_PUBLIC_AI_AGENT_URL || "http://localhost:8002",
  },
};

export default nextConfig;

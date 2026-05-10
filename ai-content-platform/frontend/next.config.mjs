/** @type {import('next').NextConfig} */
const backend = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      { source: "/api/backend/:path*", destination: `${backend}/:path*` },
    ];
  },
};

export default nextConfig;

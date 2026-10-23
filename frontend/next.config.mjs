/** @type {import('next').NextConfig} */
const backendApiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendApiUrl}/api/v1/:path*`,
      },
      {
        source: "/ws/:path*",
        destination: `${backendApiUrl}/ws/:path*`,
      },
    ];
  },
};

export default nextConfig;

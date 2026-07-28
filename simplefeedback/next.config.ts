import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [{ protocol: "https", hostname: "avatars.githubusercontent.com" }],
  },
  serverExternalPackages: ["@prisma/client"],
  turbopack: {},
};

export default nextConfig;

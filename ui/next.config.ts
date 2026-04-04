import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // enables minimal runtime bundle for Docker
};

export default nextConfig;

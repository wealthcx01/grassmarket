/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Loop 0 shell — keep config minimal and explicit. Add rewrites/headers as the
  // backend contract firms up. NEXT_PUBLIC_API_BASE_URL is read at runtime in lib/api.ts.
};

export default nextConfig;

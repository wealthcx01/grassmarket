/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Loop 0 shell — keep config minimal and explicit. Add rewrites/headers as the
  // backend contract firms up. NEXT_PUBLIC_API_BASE_URL is read at runtime in lib/api.ts.

  // GRS-0143: cold users (and the Help copy) reach for plausible top-level URLs that don't exist —
  // /academy actually lives under /workbench, and deliverables are opened from an engagement. Send
  // those guesses to their real home instead of a hard 404 (stress-test finding: 4/5 personas).
  async redirects() {
    return [
      { source: "/academy", destination: "/workbench/academy", permanent: true },
      { source: "/academy/:slug", destination: "/workbench/academy/:slug", permanent: true },
      { source: "/courses", destination: "/workbench/courses", permanent: true },
      { source: "/deliverables", destination: "/engagements", permanent: false },
    ];
  },
};

export default nextConfig;

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Loop 0 shell — keep config minimal and explicit. Add rewrites/headers as the
  // backend contract firms up. NEXT_PUBLIC_API_BASE_URL is read at runtime in lib/api.ts.

  // GRS-0143: cold users reach for plausible top-level URLs that don't exist — /academy actually
  // lives under /workbench. Send those guesses to their real home instead of a hard 404.
  // (The /deliverables redirect was removed in GRS-0186, which adds a real deliverables index page.)
  async redirects() {
    return [
      { source: "/academy", destination: "/workbench/academy", permanent: true },
      { source: "/academy/:slug", destination: "/workbench/academy/:slug", permanent: true },
      { source: "/courses", destination: "/workbench/courses", permanent: true },
      // GRS-0175: /help merged into /guide (one canonical Guide). Section ids are preserved, so
      // /help#anchor deep links resolve to the same content under /guide.
      { source: "/help", destination: "/guide", permanent: true },
    ];
  },
};

export default nextConfig;

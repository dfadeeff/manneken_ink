import { clerkMiddleware } from "@clerk/nextjs/server";

// Next 16 renamed the middleware convention to `proxy`.
export default clerkMiddleware();

export const config = {
  matcher: [
    // Everything except Next internals and static assets, plus all API routes.
    // Clerk documents a matcher with a nested group that Next 16 rejects, so
    // this is Next's own documented exclusion pattern instead.
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|woff2?|ttf|css|js)$).*)",
    "/(api|trpc)(.*)",
  ],
};

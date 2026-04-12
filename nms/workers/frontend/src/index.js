import { handleApiRequest } from "./api.js";

const SPA_FALLBACK = "/index.html";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/api" || url.pathname.startsWith("/api/")) {
      return handleApiRequest(request, env);
    }

    let response = await env.ASSETS.fetch(request);

    if (response.status === 404 && request.method === "GET" && !url.pathname.includes(".")) {
      const spaRequest = new Request(new URL(SPA_FALLBACK, url.origin).toString(), request);
      response = await env.ASSETS.fetch(spaRequest);
    }

    const headers = new Headers(response.headers);
    headers.set("X-Frame-Options", "SAMEORIGIN");
    headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
    headers.set("X-Content-Type-Options", "nosniff");

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  },
};

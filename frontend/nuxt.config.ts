export default defineNuxtConfig({
  devtools: { enabled: true },
  css: ["~/assets/css/main.css"],
  runtimeConfig: {
    // Defaults used at build time. At runtime, Docker must set NUXT_BACKEND_BASE_URL (see docker-compose).
    // BACKEND_BASE_URL is supported for local dev / custom runs where env is read at process start.
    backendBaseUrl:
      process.env.NUXT_BACKEND_BASE_URL ||
      process.env.BACKEND_BASE_URL ||
      "http://127.0.0.1:8000",
    /** Forwarded as X-Internal-Secret (must match RYW_INTERNAL_API_SECRET on FastAPI). */
    internalApiSecret:
      process.env.NUXT_INTERNAL_API_SECRET || process.env.RYW_INTERNAL_API_SECRET || ""
  },
  app: {
    head: {
      title: "Ride YourWay Market Dashboard",
      meta: [
        {
          name: "viewport",
          content: "width=device-width, initial-scale=1"
        },
        {
          name: "description",
          content:
            "Dummy Ride YourWay dashboard built from extracted operational data and a prospective intake example."
        }
      ],
      link: [{ rel: "icon", type: "image/png", href: "/favicon.png" }]
    }
  }
})

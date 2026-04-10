import { getHeader, getMethod, readBody } from "h3"

const MAX_PATH_LEN = 2048

function assertAllowedBackendPath(endpoint: string): void {
  const p = endpoint.replace(/^\/+/u, "").replace(/\/+$/u, "")
  if (!p || p.length > MAX_PATH_LEN) {
    throw createError({ statusCode: 400, statusMessage: "Invalid backend path" })
  }
  if (p.includes("..") || p.includes("\\")) {
    throw createError({ statusCode: 400, statusMessage: "Invalid backend path" })
  }
  if (p === "health" || p === "ready") return
  if (p.startsWith("api/v1/")) return
  if (p === "openapi.json" || p === "redoc" || p === "docs" || p.startsWith("docs/")) return
  throw createError({ statusCode: 404, statusMessage: "Backend route not allowed" })
}

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const rawPath = event.context.params?.path || ""
  const endpoint = Array.isArray(rawPath) ? rawPath.join("/") : rawPath
  assertAllowedBackendPath(endpoint)

  const method = getMethod(event)
  const url = `${config.backendBaseUrl.replace(/\/+$/u, "")}/${endpoint}`
  const role = getHeader(event, "x-role") || "analyst"
  const body = method === "GET" ? undefined : await readBody(event)

  const headers: Record<string, string> = { "X-Role": role }
  const secret = config.internalApiSecret as string | undefined
  if (secret) headers["X-Internal-Secret"] = secret

  try {
    const data = await $fetch(url, {
      method,
      headers,
      body,
      retry: 0,
      timeout: 60_000
    })
    return data
  } catch (error: any) {
    const status =
      typeof error?.statusCode === "number"
        ? error.statusCode
        : typeof error?.response?.status === "number"
          ? error.response.status
          : undefined
    const causeCode = error?.cause?.code as string | undefined
    const messageLower = String(error?.message ?? "").toLowerCase()
    const unreachable =
      causeCode === "ECONNREFUSED" ||
      causeCode === "ENOTFOUND" ||
      messageLower.includes("econnrefused") ||
      messageLower.includes("fetch failed")

    const hint = unreachable
      ? `Cannot reach API at ${url.split("/").slice(0, 3).join("/")}. Start the backend (docker compose from repo root). In Docker the Nuxt server needs NUXT_BACKEND_BASE_URL=http://backend:8000 (set in compose); local "nuxt dev" uses http://127.0.0.1:8000 by default.`
      : undefined

    throw createError({
      statusCode: status && status >= 400 ? status : 502,
      statusMessage: unreachable ? "API unreachable" : error?.statusMessage || "Backend request failed",
      data: hint ? { ...error?.data, message: hint } : error?.data
    })
  }
})

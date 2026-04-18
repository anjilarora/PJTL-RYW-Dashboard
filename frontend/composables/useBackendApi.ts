import type { ApiEnvelope, Role } from "~/types/api"

export interface ApiClientError {
  code: string
  message: string
  statusCode?: number
}

export function useBackendApi() {
  const role = useState<Role>("role", () => "admin")
  const lastError = useState<ApiClientError | null>("backend-api-last-error", () => null)

  async function requestWithResilience<T>(
    path: string,
    options: { method?: "GET" | "POST" | "PUT"; body?: Record<string, unknown> } = {}
  ) {
    let attempt = 0
    const maxAttempts = 2
    while (attempt < maxAttempts) {
      try {
        const res = await $fetch<ApiEnvelope<T>>(path, {
          method: options.method,
          headers: { "X-Role": role.value },
          body: options.body,
          timeout: 10_000
        })
        lastError.value = null
        return res
      } catch (error: any) {
        attempt += 1
        const statusCode = Number(error?.statusCode ?? error?.status ?? 0)
        const retriable = statusCode === 0 || statusCode >= 500
        lastError.value = {
          code: "BACKEND_REQUEST_FAILED",
          message: error?.data?.error?.message ?? error?.message ?? "Backend request failed",
          statusCode
        }
        if (!retriable || attempt >= maxAttempts) {
          throw error
        }
      }
    }
    throw new Error("Unexpected request loop exit")
  }

  async function apiGet<T>(path: string) {
    return await requestWithResilience<T>(path)
  }

  async function apiPost<T>(path: string, body: Record<string, unknown>) {
    return await requestWithResilience<T>(path, { method: "POST", body })
  }

  async function apiPut<T>(path: string, body: Record<string, unknown>) {
    return await requestWithResilience<T>(path, { method: "PUT", body })
  }

  return { role, lastError, apiGet, apiPost, apiPut }
}

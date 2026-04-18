import { getHeader, readMultipartFormData } from "h3"

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const parts = await readMultipartFormData(event)
  const file = parts?.find((p) => p.name === "file")
  if (!file?.data?.length) {
    throw createError({ statusCode: 400, statusMessage: "Missing file field" })
  }

  const blob = new Blob([new Uint8Array(file.data)], {
    type: file.type || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  })
  const fd = new FormData()
  fd.append("file", blob, file.filename || "intake.xlsx")

  const role = getHeader(event, "x-role") || "admin"
  const headers: Record<string, string> = { "X-Role": role }
  const secret = config.internalApiSecret as string | undefined
  if (secret) headers["X-Internal-Secret"] = secret

  const base = config.backendBaseUrl.replace(/\/+$/u, "")
  return await $fetch(`${base}/api/v1/jobs/intake-upload`, {
    method: "POST",
    body: fd,
    headers,
    timeout: 120_000
  })
})

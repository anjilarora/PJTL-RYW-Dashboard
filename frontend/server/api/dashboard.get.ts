import { dashboardData } from "../utils/dashboardData"

export default defineEventHandler(async () => {
  const config = useRuntimeConfig()
  let backendStatus = "unreachable"
  try {
    const health = await $fetch<{ data?: { status?: string } }>(`${config.backendBaseUrl}/health`)
    backendStatus = health?.data?.status || "ok"
  } catch {
    backendStatus = "unreachable"
  }
  return {
    ...dashboardData,
    sourceNote: `${dashboardData.sourceNote} Backend API status: ${backendStatus}.`
  }
})

/**
 * Operational Deep Dive composable.
 *
 * Each helper lazily GETs the matching ``/api/v1/dashboard/*`` endpoint
 * exposed by ``code/backend/api/routes/operational.py``. Data is cached in a
 * shared ``useState`` slot so switching between tabs (or re-opening the
 * Operational Deep Dive) is instantaneous after the first request.
 *
 * Each loader also exposes ``loading`` and ``error`` refs so panel components
 * can render skeletons / friendly errors without re-implementing the fetch
 * state machine.
 */

export interface OperationalLoader<T> {
  data: Ref<T | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  load: () => Promise<void>
  reload: () => Promise<void>
}

function makeLoader<T>(key: string, path: string): OperationalLoader<T> {
  const data = useState<T | null>(`ops-${key}`, () => null)
  const loading = useState<boolean>(`ops-${key}-loading`, () => false)
  const error = useState<string | null>(`ops-${key}-error`, () => null)
  const { apiGet } = useBackendApi()

  async function fetchData() {
    loading.value = true
    error.value = null
    try {
      const res = await apiGet<T>(path)
      data.value = (res as unknown as { data: T }).data
    } catch (e: unknown) {
      const err = e as { statusCode?: number; data?: { detail?: { message?: string } }; message?: string }
      if (err?.statusCode === 404) {
        error.value = err?.data?.detail?.message ?? "Operational EDA artifact missing. Run the operational_eda notebook to regenerate."
      } else {
        error.value = err?.message ?? "Request failed."
      }
      data.value = null
    } finally {
      loading.value = false
    }
  }

  return {
    data,
    loading,
    error,
    async load() {
      if (data.value !== null || loading.value) return
      await fetchData()
    },
    async reload() {
      await fetchData()
    }
  }
}

export function useFleetScorecard() {
  return makeLoader<{ regions: Array<{ region: string; gates: Array<Record<string, unknown>> }> }>(
    "fleet-scorecard",
    "/api/backend/api/v1/dashboard/fleet-scorecard"
  )
}

export function useWeeklyTrend() {
  return makeLoader<{ weeks: Array<Record<string, unknown>> }>(
    "weekly-trend",
    "/api/backend/api/v1/dashboard/weekly-trend"
  )
}

export function useModeProfitability() {
  return makeLoader<{ modes: Array<Record<string, unknown>> }>(
    "mode-profitability",
    "/api/backend/api/v1/dashboard/mode-profitability"
  )
}

export function useOtpMatrix() {
  return makeLoader<{ rows: Array<Record<string, unknown>> }>(
    "otp",
    "/api/backend/api/v1/dashboard/otp"
  )
}

export function usePayerConcentration() {
  return makeLoader<{
    payers: Array<Record<string, unknown>>
    warnings: Array<Record<string, unknown>>
    cap_volume: number
    cap_revenue: number
  }>("payer-concentration", "/api/backend/api/v1/dashboard/payer-concentration")
}

export function useHourlyDemand() {
  return makeLoader<{
    rows: Array<Record<string, unknown>>
    idle_windows: Array<Record<string, unknown>>
  }>("hourly-demand", "/api/backend/api/v1/dashboard/hourly-demand")
}

export function useCancellations() {
  return makeLoader<{
    rows: Array<Record<string, unknown>>
    by_reason: Array<{ key: string; count: number }>
    by_mode: Array<{ key: string; count: number }>
    by_day: Array<{ key: string; count: number }>
    by_payer: Array<{ key: string; count: number }>
    total: number
  }>("cancellations", "/api/backend/api/v1/dashboard/cancellations")
}

export function useRevPerKentleg() {
  return makeLoader<{
    payers: Array<Record<string, unknown>>
    target: number
    fleet_rev_per_kentleg: number | null
  }>("rev-per-kl", "/api/backend/api/v1/dashboard/rev-per-kl")
}

export function useSecureCareCompare() {
  return makeLoader<{
    streams: Record<
      string,
      {
        total_revenue: number
        total_cost: number
        net_margin: number
        margin_pct: number | null
        weeks: Array<Record<string, unknown>>
      }
    >
  }>("securecare", "/api/backend/api/v1/dashboard/securecare-compare")
}

export function useRegionalCost() {
  return makeLoader<{
    regions: Array<Record<string, unknown>>
    target_cost_per_road_hour: number
    is_estimate: boolean
  }>("cost-regional", "/api/backend/api/v1/dashboard/cost-regional")
}

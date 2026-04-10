/** Shared session keys and default market payload for viability API calls. */

export const RYW_STORAGE_MARKET = "ryw_viability_market"
export const RYW_STORAGE_HISTORICAL = "ryw_viability_historical"

export function defaultMarketProfile() {
  return {
    region: { region_name: "Grand Rapids North Corridor", state: "MI" },
    fleet: {
      wheelchair_vehicles: 2,
      ambulatory_vehicles: 2,
      stretcher_vehicles: 1,
      securecare_vehicles: 1,
      drivers: 8
    },
    prospective_contracts: [] as unknown[]
  }
}

export function buildEvaluatePayloadFromSession(): {
  market_profile: Record<string, unknown>
  historical_data: Record<string, unknown>
} {
  if (import.meta.client) {
    const rawM = sessionStorage.getItem(RYW_STORAGE_MARKET)
    const rawH = sessionStorage.getItem(RYW_STORAGE_HISTORICAL)
    if (rawM) {
      try {
        const market_profile = JSON.parse(rawM) as Record<string, unknown>
        let historical_data: Record<string, unknown> = {}
        if (rawH) historical_data = JSON.parse(rawH) as Record<string, unknown>
        return { market_profile, historical_data }
      } catch {
        /* fall through */
      }
    }
  }
  return { market_profile: defaultMarketProfile() as unknown as Record<string, unknown>, historical_data: {} }
}

export function clearViabilitySession(): void {
  if (!import.meta.client) return
  sessionStorage.removeItem(RYW_STORAGE_MARKET)
  sessionStorage.removeItem(RYW_STORAGE_HISTORICAL)
}

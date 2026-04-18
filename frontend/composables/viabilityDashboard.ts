/** Map backend viability payload into dashboard panel shapes (live vs static demo data). */

export type GateRow = {
  name: string
  threshold: string
  value: string
  status: "pass" | "fail" | "provisional"
  confidence: string
  note: string
}

export type ViabilityLike = {
  report?: {
    region?: string
    go_decision?: boolean
    projected_margin?: number
    passing?: number
    failing?: number
    conditions?: Array<{
      metric: number
      name: string
      target: string
      actual: number
      passed: boolean
    }>
  }
  gate_details?: Array<{
    metric: number
    name: string
    confidence_tier?: string
    formula_version?: string
  }>
}

function formatConditionActual(metric: number, actual: number): string {
  if (metric === 4 || metric === 9) return `$${actual.toFixed(2)}`
  if (metric === 7) return `${actual.toFixed(2)}`
  return `${(actual * 100).toFixed(1)}%`
}

function gateStatusFromCondition(passed: boolean, confidence: string): GateRow["status"] {
  if (!passed) return "fail"
  if (confidence.includes("Tier 2") || confidence.includes("Tier 3")) return "provisional"
  return "pass"
}

export function gatesFromViability(v: ViabilityLike | null | undefined, fallback: GateRow[]): GateRow[] {
  const conds = v?.report?.conditions
  if (!conds?.length) return fallback
  const details = v.gate_details ?? []
  return conds.map((c) => {
    const gd = details.find((d) => d.metric === c.metric)
    const confidence = gd?.confidence_tier ?? "Tier 1 Audited"
    return {
      name: c.name,
      threshold: c.target,
      value: formatConditionActual(c.metric, c.actual),
      status: gateStatusFromCondition(c.passed, confidence),
      confidence,
      note: `${gd?.formula_version ?? "v1"} · engine evaluation`,
    }
  })
}

export function marketFromViability(
  v: ViabilityLike | null | undefined,
  fallback: { name: string; summary: string; status?: string; confidence?: string }
) {
  if (!v?.report?.region) return fallback
  const go = v.report.go_decision
  const passing = v.report.passing ?? 0
  const failing = v.report.failing ?? 0
  const total = passing + failing || 9
  const summary = go
    ? `This market meets every launch readiness check based on the Q1 2026 reference data. All ${total} gates are passing.`
    : `This market isn't ready to launch yet. Based on the Q1 2026 reference data, ${passing} of ${total} readiness gates pass and ${failing} fall short of their target.`
  return {
    name: v.report.region,
    summary,
    status: go ? "Go" : "No-Go",
    confidence: undefined,
  }
}

export function readinessFromViability(
  v: ViabilityLike | null | undefined,
  staticReadiness: {
    score: number
    passingCount: number
    provisionalCount: number
    failingCount: number
    totalConditions: number
    projectedMarginPct: number
    targetMarginPct: number
    projectedWeeklyRevenue: number
    projectedRevenuePerKentLeg: number
    targetRevenuePerKentLeg: number
    projectedRoadHoursPerVehicleDay: number
    projectedHigherAcuitySharePct: number
    decisionNote: string
  }
) {
  const cond = (n: number) => v?.report?.conditions?.find((c) => c.metric === n)
  if (!v?.report?.conditions?.length) return staticReadiness
  const c4 = cond(4)
  const c5 = cond(5)
  const c7 = cond(7)
  const baseRkl = staticReadiness.projectedRevenuePerKentLeg || 1
  const liveRkl = c4 ? c4.actual : baseRkl
  const scale = liveRkl / baseRkl
  const marginPct =
    typeof v.report.projected_margin === "number" ? v.report.projected_margin * 100 : staticReadiness.projectedMarginPct
  return {
    ...staticReadiness,
    passingCount: v.report.passing ?? staticReadiness.passingCount,
    failingCount: v.report.failing ?? staticReadiness.failingCount,
    provisionalCount: Math.max(
      0,
      staticReadiness.totalConditions - (v.report.passing ?? 0) - (v.report.failing ?? 0)
    ),
    projectedMarginPct: marginPct,
    projectedWeeklyRevenue: staticReadiness.projectedWeeklyRevenue * scale,
    projectedRevenuePerKentLeg: liveRkl,
    projectedRoadHoursPerVehicleDay: c7 ? c7.actual : staticReadiness.projectedRoadHoursPerVehicleDay,
    projectedHigherAcuitySharePct: c5 ? c5.actual * 100 : staticReadiness.projectedHigherAcuitySharePct,
    decisionNote:
      "Key gate metrics reflect the latest viability run. Narrative driver cards may still use static intake context.",
  }
}

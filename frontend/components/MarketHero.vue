<script setup lang="ts">
type Readiness = {
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

const props = defineProps<{
  name: string
  cityState?: string
  corridor?: string
  status: string
  confidence?: string
  summary: string
  readiness: Readiness
}>()

const statusKey = computed(() => {
  const s = (props.status || "").toLowerCase()
  if (s.includes("no")) return "no-go"
  if (s.includes("go")) return "go"
  return "neutral"
})

const ringPct = computed(() => Math.max(0, Math.min(100, props.readiness.score)))
const ringDash = computed(() => (ringPct.value / 100) * 2 * Math.PI * 52)
const ringCircumference = 2 * Math.PI * 52

const tone = computed(() => {
  if (statusKey.value === "go") return "pass"
  if (statusKey.value === "no-go") return "fail"
  return "provisional"
})
</script>

<template>
  <section class="hero" :class="`hero--${statusKey}`" aria-label="Market readiness hero">
    <div class="hero__left">
      <div class="hero__eyebrow">
        <span class="hero__pill hero__pill--brand">Market readiness</span>
        <span v-if="corridor" class="hero__corridor">{{ corridor }}<span v-if="cityState"> · {{ cityState }}</span></span>
      </div>
      <h1 class="hero__title">{{ name }}</h1>
      <p class="hero__summary">{{ summary }}</p>
      <div class="hero__chips">
        <span class="hero__chip hero__chip--pass">
          <span class="hero__chip-dot" />
          {{ readiness.passingCount }} pass
        </span>
        <span class="hero__chip hero__chip--prov">
          <span class="hero__chip-dot" />
          {{ readiness.provisionalCount }} provisional
        </span>
        <span class="hero__chip hero__chip--fail">
          <span class="hero__chip-dot" />
          {{ readiness.failingCount }} fail
        </span>
        <span v-if="confidence" class="hero__chip hero__chip--meta">{{ confidence }}</span>
      </div>
    </div>

    <div class="hero__right">
      <div class="hero__ring" :class="`hero__ring--${tone}`" role="img" :aria-label="`Readiness score ${ringPct.toFixed(0)} percent`">
        <svg viewBox="0 0 120 120" width="168" height="168">
          <circle cx="60" cy="60" r="52" fill="none" stroke="var(--line)" stroke-width="10" opacity="0.5" />
          <circle
            cx="60"
            cy="60"
            r="52"
            fill="none"
            stroke="currentColor"
            stroke-width="10"
            stroke-linecap="round"
            :stroke-dasharray="`${ringDash} ${ringCircumference}`"
            transform="rotate(-90 60 60)"
          />
        </svg>
        <div class="hero__ring-center">
          <strong>{{ ringPct.toFixed(0) }}<span>%</span></strong>
          <span class="hero__ring-label">readiness</span>
        </div>
      </div>
      <div class="hero__status" :class="`hero__status--${statusKey}`">
        <span class="hero__status-label">Decision</span>
        <strong>{{ status }}</strong>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(240px, 0.9fr);
  gap: 28px;
  padding: 26px 28px;
  border-radius: 28px;
  border: 1px solid var(--line);
  background:
    radial-gradient(circle at 0% 0%, var(--maize-soft), transparent 55%),
    radial-gradient(circle at 100% 100%, var(--blue-soft), transparent 50%),
    var(--surface);
  box-shadow: var(--shadow);
  overflow: hidden;
}
.hero::before {
  content: "";
  position: absolute;
  inset: auto 0 0 0;
  height: 4px;
  background: linear-gradient(90deg, var(--blue), var(--maize));
  opacity: 0.9;
}
.hero__left {
  min-width: 0;
}
.hero__eyebrow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.hero__pill {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.hero__pill--brand {
  background: var(--maize-soft);
  color: var(--maize-ink);
  border: 1px solid color-mix(in srgb, var(--maize) 40%, transparent);
}
.hero__corridor {
  font-size: 0.88rem;
  color: var(--muted);
  font-weight: 600;
}
.hero__title {
  margin: 0;
  font-size: clamp(1.55rem, 2.4vw, 2.1rem);
  letter-spacing: -0.04em;
  line-height: 1.1;
  color: var(--ink);
}
.hero__summary {
  margin: 10px 0 16px;
  color: var(--muted);
  font-size: 0.98rem;
  line-height: 1.55;
  max-width: 58ch;
}
.hero__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.hero__chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 700;
  background: var(--surface-2);
  border: 1px solid var(--line);
  color: var(--ink);
}
.hero__chip-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
}
.hero__chip--pass .hero__chip-dot { background: var(--teal); }
.hero__chip--prov .hero__chip-dot { background: var(--amber); }
.hero__chip--fail .hero__chip-dot { background: var(--red); }
.hero__chip--meta {
  background: var(--blue-soft);
  color: var(--blue);
  border-color: color-mix(in srgb, var(--blue) 30%, var(--line));
}

.hero__right {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
}
.hero__ring {
  position: relative;
  width: 168px;
  height: 168px;
  color: var(--blue);
}
.hero__ring--pass { color: var(--teal); }
.hero__ring--fail { color: var(--red); }
.hero__ring--provisional { color: var(--amber); }

.hero__ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  text-align: center;
  padding: 0 8px;
}
.hero__ring-center strong {
  display: block;
  font-size: 2.4rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--ink);
  line-height: 1;
}
.hero__ring-center strong span {
  font-size: 1rem;
  font-weight: 600;
  color: var(--muted);
  margin-left: 2px;
  vertical-align: baseline;
}
.hero__ring-label {
  display: block;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--muted);
}
.hero__status {
  display: grid;
  place-items: center;
  padding: 10px 20px;
  border-radius: 14px;
  border: 1px solid var(--line);
  min-width: 140px;
}
.hero__status-label {
  font-size: 0.72rem;
  color: var(--muted);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.hero__status strong {
  font-size: 1.15rem;
  letter-spacing: -0.02em;
}
.hero__status--go {
  background: var(--teal-soft);
  border-color: color-mix(in srgb, var(--teal) 35%, var(--line));
  color: var(--teal);
}
.hero__status--no-go {
  background: var(--red-soft);
  border-color: color-mix(in srgb, var(--red) 35%, var(--line));
  color: var(--red);
}
.hero__status--neutral {
  background: var(--surface-2);
  color: var(--ink);
}

@media (max-width: 980px) {
  .hero {
    grid-template-columns: 1fr;
    gap: 18px;
    padding: 22px 20px;
  }
  .hero__right {
    flex-direction: row;
    justify-content: space-between;
    width: 100%;
  }
}
</style>

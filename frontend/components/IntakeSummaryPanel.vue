<script setup lang="ts">
const props = defineProps<{
  programs: Array<{
    program: string
    tripMode: string
    weeklyTrips: number
    kentLegs: number
    avgRevenuePerKentLeg: number
    volumeClass: string
    scheduling: string
  }>
}>()

const totals = computed(() => {
  const classCounts: Record<string, number> = {}
  const classTrips: Record<string, number> = {}
  let weeklyTrips = 0
  let kentLegs = 0
  let qualityTrips = 0
  for (const p of props.programs) {
    classCounts[p.volumeClass] = (classCounts[p.volumeClass] || 0) + 1
    classTrips[p.volumeClass] = (classTrips[p.volumeClass] || 0) + p.weeklyTrips
    weeklyTrips += p.weeklyTrips
    kentLegs += p.kentLegs
    if (p.volumeClass === "Quality") qualityTrips += p.weeklyTrips
  }
  const qualityPct = weeklyTrips ? (qualityTrips / weeklyTrips) * 100 : 0
  return {
    programs: props.programs.length,
    weeklyTrips,
    kentLegs,
    qualityPct,
    classCounts,
    classTrips
  }
})

const qualityStatus = computed(() => {
  const pct = totals.value.qualityPct
  if (pct >= 90) return { tone: "pass", label: "Meets the 90% quality-mix target." }
  if (pct >= 80) return { tone: "warn", label: `Below the 90% target by ${(90 - pct).toFixed(1)} pts. Add quality-volume lines or reduce filler.` }
  return { tone: "fail", label: `Well below the 90% target. Concentration in filler / broker volume is the main blocker to launch.` }
})
</script>

<template>
  <article class="panel intake-panel">
    <div class="panel-eyebrow">
      Intake Summary
      <InfoTip
        label="About the intake summary"
        content="This panel rolls up every prospective program in the current market intake. It tells you how much weekly volume is committed, how it splits across program types (Quality vs Filler vs Broker), and whether the mix clears the 90% quality-share target that the launch playbook requires."
      />
    </div>
    <h2>Prospective Intake Overview</h2>
    <p class="intake-lead">
      The prospective market has <strong>{{ totals.programs }}</strong> programs worth
      <strong>{{ totals.weeklyTrips }}</strong> trips / week (<strong>{{ totals.kentLegs.toFixed(1) }}</strong> Kent-Legs).
      Quality-volume share is <strong>{{ totals.qualityPct.toFixed(1) }}%</strong>.
    </p>

    <div class="intake-takeaway" :class="`intake-takeaway--${qualityStatus.tone}`" role="note">
      <span class="intake-takeaway__label">Takeaway</span>
      <span class="intake-takeaway__text">{{ qualityStatus.label }}</span>
    </div>

    <div class="intake-breakdown" aria-label="Program class breakdown">
      <div v-for="(count, klass) in totals.classCounts" :key="klass" class="intake-chip">
        <span class="intake-chip__class">{{ klass }}</span>
        <span class="intake-chip__value">{{ count }} programs · {{ totals.classTrips[klass] }} trips/wk</span>
      </div>
    </div>

    <h3 class="intake-subhead">Programs in the intake</h3>
    <div class="subpanels">
      <div class="subpanel" v-for="program in programs" :key="program.program">
        <div class="subpanel-title">{{ program.program }}</div>
        <p class="subpanel-line">
          <span class="subpanel-pill" :class="`subpanel-pill--${program.volumeClass.toLowerCase()}`">{{ program.volumeClass }}</span>
          <span>{{ program.tripMode }}</span>
          <span>{{ program.weeklyTrips }} trips/week</span>
          <span>${{ program.avgRevenuePerKentLeg.toFixed(2) }} / Kent-Leg</span>
        </p>
        <p class="subpanel-meta">{{ program.scheduling }}</p>
      </div>
    </div>
  </article>
</template>

<style scoped>
.intake-lead {
  margin: 6px 0 14px;
  color: var(--ink);
  line-height: 1.55;
  max-width: 62ch;
}

.intake-takeaway {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  align-items: baseline;
  padding: 12px 14px;
  border-radius: 10px;
  margin-bottom: 14px;
  border-left: 4px solid var(--line-strong);
  background: var(--surface-2);
}

.intake-takeaway__label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}

.intake-takeaway__text {
  color: var(--ink);
  font-size: 0.93rem;
  line-height: 1.5;
}

.intake-takeaway--pass {
  border-left-color: var(--teal);
}
.intake-takeaway--pass .intake-takeaway__label { color: var(--teal); }

.intake-takeaway--warn {
  border-left-color: var(--amber);
}
.intake-takeaway--warn .intake-takeaway__label { color: var(--amber); }

.intake-takeaway--fail {
  border-left-color: var(--red);
}
.intake-takeaway--fail .intake-takeaway__label { color: var(--red); }

.intake-breakdown {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.intake-chip {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  font-size: 0.82rem;
}

.intake-chip__class {
  font-weight: 700;
  color: var(--ink);
}

.intake-chip__value {
  color: var(--muted);
}

.intake-subhead {
  margin: 18px 0 10px;
  font-size: 0.92rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
}

.subpanel-line {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  align-items: center;
  margin: 6px 0 4px;
  color: var(--ink);
  font-size: 0.9rem;
}

.subpanel-meta {
  margin: 2px 0 0;
  color: var(--muted);
  font-size: 0.82rem;
}

.subpanel-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: var(--surface-3);
  color: var(--muted);
  border: 1px solid var(--line);
}
.subpanel-pill--quality {
  background: var(--blue-soft);
  color: var(--blue);
  border-color: transparent;
}
.subpanel-pill--filler {
  background: var(--teal-soft);
  color: var(--teal);
  border-color: transparent;
}
.subpanel-pill--broker {
  background: var(--amber-soft);
  color: var(--amber);
  border-color: transparent;
}

.panel-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
</style>

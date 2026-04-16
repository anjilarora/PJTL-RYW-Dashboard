<script setup lang="ts">
/**
 * Full detail view for a single gate row.
 * Rendered inside the detail tabs so the scorecard stays compact and the
 * full story for the selected gate gets its own "Gate detail" tab.
 */
type Row = {
  name: string
  threshold: string
  value: string
  status: "pass" | "fail" | "provisional"
  confidence: string
  note: string
}

defineProps<{
  row?: Row
  totalCount?: number
  index?: number
}>()

const confidenceExplain = (confidence: string) => {
  const n = confidence.match(/Tier\s*(\d+)/i)?.[1]
  if (n === "1") return "Tier 1 Audited — validated against historical behavior and a stable formula."
  if (n === "2") return "Tier 2 Assumption-Backed — partially validated; formula still has unresolved definitions."
  if (n === "3") return "Tier 3 Manual Override — value entered by an analyst; must be validated before launch."
  return confidence
}
</script>

<template>
  <section
    v-if="row"
    class="panel gate-detail"
    :class="`gate-detail--${row.status}`"
    aria-label="Selected gate detail"
  >
    <div class="gate-detail__head">
      <div>
        <div class="panel-eyebrow">
          Gate detail
        </div>
        <h3>{{ row.name }}</h3>
        <p v-if="typeof index === 'number' && totalCount" class="gate-detail__counter">
          Gate {{ index + 1 }} of {{ totalCount }} on the launch scorecard.
        </p>
      </div>
      <StatusPill :label="row.status" :tone="row.status" />
    </div>

    <dl class="gate-detail__grid">
      <div>
        <dt>Current value</dt>
        <dd class="gate-detail__value">{{ row.value }}</dd>
      </div>
      <div>
        <dt>Threshold</dt>
        <dd>{{ row.threshold }}</dd>
      </div>
      <div>
        <dt>Confidence</dt>
        <dd :title="confidenceExplain(row.confidence)">{{ row.confidence }}</dd>
      </div>
    </dl>

    <p class="gate-detail__note">{{ row.note }}</p>
    <p class="gate-detail__confidence-hint">{{ confidenceExplain(row.confidence) }}</p>
  </section>

  <section v-else class="panel gate-detail gate-detail--empty">
    <p>No gate selected. Pick a card in the scorecard above.</p>
  </section>
</template>

<style scoped>
.gate-detail {
  padding: 18px 22px;
  border-left: 4px solid var(--line-strong);
}
.gate-detail--pass { border-left-color: var(--teal); }
.gate-detail--fail { border-left-color: var(--red); }
.gate-detail--provisional { border-left-color: var(--amber); }

.gate-detail--empty {
  color: var(--muted);
  font-style: italic;
}

.gate-detail__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.gate-detail__head h3 {
  margin: 4px 0 0;
  font-size: clamp(1.1rem, 1.6vw, 1.35rem);
  letter-spacing: -0.02em;
}
.gate-detail__counter {
  margin: 4px 0 0;
  font-size: 0.82rem;
  color: var(--muted);
}
.gate-detail__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px 16px;
  margin: 0 0 12px;
}
.gate-detail__grid dt {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted-2);
  margin: 0 0 2px;
}
.gate-detail__grid dd {
  margin: 0;
  font-size: 0.95rem;
  color: var(--ink);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.gate-detail__value {
  font-size: 1.2rem !important;
  letter-spacing: -0.02em;
}
.gate-detail__note {
  margin: 0 0 8px;
  color: var(--ink);
  line-height: 1.6;
  font-size: 0.98rem;
}
.gate-detail__confidence-hint {
  margin: 0;
  color: var(--muted);
  font-size: 0.85rem;
  line-height: 1.55;
}
</style>

<script setup lang="ts">
/**
 * Launch readiness gate scorecard — carousel layout.
 *
 * Each gate is a compact, clickable card in a horizontal scroll-snap track.
 * Prev / next buttons step through cards one at a time; clicking any card
 * opens an inline detail pane below with the full note, threshold wording,
 * and confidence explanation. This keeps the scorecard skimmable at a glance
 * while still surfacing every detail that used to live in the table.
 */
type GateRow = {
  name: string
  threshold: string
  value: string
  status: "pass" | "fail" | "provisional"
  confidence: string
  note: string
}

const props = defineProps<{
  rows: GateRow[]
  compact?: boolean
}>()

const emit = defineEmits<{
  (e: "gate-selected", index: number): void
}>()

const selectedIndex = ref(0)

const totals = computed(() => {
  const counts = { pass: 0, fail: 0, provisional: 0 }
  for (const r of props.rows) counts[r.status] += 1
  return counts
})

const selected = computed<GateRow | undefined>(() => props.rows[selectedIndex.value])

const confidenceTierShort = (confidence: string) => {
  const match = confidence.match(/Tier\s*(\d+)/i)
  if (match) return `T${match[1]}`
  return confidence
}

const confidenceExplain = (confidence: string) => {
  const n = confidence.match(/Tier\s*(\d+)/i)?.[1]
  if (n === "1") return "Tier 1 Audited — validated against historical behavior and a stable formula."
  if (n === "2") return "Tier 2 Assumption-Backed — partially validated; formula still has unresolved definitions."
  if (n === "3") return "Tier 3 Manual Override — value entered by an analyst; must be validated before launch."
  return confidence
}

const track = ref<HTMLElement | null>(null)

function scrollCardIntoView(idx: number) {
  nextTick(() => {
    const el = track.value?.querySelectorAll<HTMLElement>(".gate-card")[idx]
    if (el) el.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" })
  })
}

function selectIndex(idx: number) {
  if (!props.rows.length) return
  const clamped = Math.max(0, Math.min(props.rows.length - 1, idx))
  selectedIndex.value = clamped
  scrollCardIntoView(clamped)
  emit("gate-selected", clamped)
}

function step(delta: number) {
  selectIndex(selectedIndex.value + delta)
}

function onCardKeydown(ev: KeyboardEvent, idx: number) {
  if (ev.key === "ArrowRight") {
    ev.preventDefault()
    selectIndex(idx + 1)
  } else if (ev.key === "ArrowLeft") {
    ev.preventDefault()
    selectIndex(idx - 1)
  } else if (ev.key === "Enter" || ev.key === " ") {
    ev.preventDefault()
    selectIndex(idx)
  }
}

/** Split "≥ 95%" or ">= $70" into a comparator symbol + target so the card can
 *  render the target in its own typographic slot. Falls back to the raw string
 *  if we do not recognise the shape. */
function splitThreshold(t: string) {
  const match = t.trim().match(/^(>=|<=|>|<|≥|≤|=)\s*(.+)$/)
  if (!match) return { comparator: "", target: t }
  const map: Record<string, string> = { ">=": "≥", "<=": "≤" }
  return { comparator: map[match[1]] ?? match[1], target: match[2] }
}
</script>

<template>
  <article class="panel gate-scorecard">
    <header class="gate-scorecard__head">
      <div class="gate-scorecard__title">
        <div class="panel-eyebrow">
          Gate scorecard
          <InfoTip
            label="How to read the scorecard"
            content="Each card is one of nine launch gates. Click a card to open its full detail below: threshold wording, current value, and the confidence tier behind the input. Use the arrows or keyboard arrow keys to step through gates."
          />
        </div>
        <h2>Launch readiness gate scorecard</h2>
      </div>
      <div class="gate-scorecard__counts" aria-label="Overall gate counts">
        <span class="gate-scorecard__count gate-scorecard__count--pass">
          <span class="dot" /> {{ totals.pass }} pass
        </span>
        <span class="gate-scorecard__count gate-scorecard__count--prov">
          <span class="dot" /> {{ totals.provisional }} provisional
        </span>
        <span class="gate-scorecard__count gate-scorecard__count--fail">
          <span class="dot" /> {{ totals.fail }} fail
        </span>
      </div>
    </header>

    <div class="gate-scorecard__carousel">
      <button
        type="button"
        class="gate-scorecard__nav gate-scorecard__nav--prev"
        :disabled="selectedIndex === 0"
        aria-label="Previous gate"
        @click="step(-1)"
      >
        <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 6l-6 6 6 6" />
        </svg>
      </button>

      <div ref="track" class="gate-scorecard__track" role="tablist" aria-label="Launch readiness gates">
        <button
          v-for="(row, idx) in rows"
          :key="row.name"
          type="button"
          role="tab"
          :id="`gate-tab-${idx}`"
          :aria-selected="selectedIndex === idx"
          :aria-controls="`gate-panel-${idx}`"
          :tabindex="selectedIndex === idx ? 0 : -1"
          class="gate-card"
          :class="[`gate-card--${row.status}`, { 'gate-card--active': selectedIndex === idx }]"
          @click="selectIndex(idx)"
          @keydown="(e) => onCardKeydown(e, idx)"
        >
          <div class="gate-card__top">
            <StatusPill :label="row.status" :tone="row.status" size="sm" />
            <span class="gate-card__conf" :title="confidenceExplain(row.confidence)">
              {{ confidenceTierShort(row.confidence) }}
            </span>
          </div>
          <div class="gate-card__name">{{ row.name }}</div>
          <div class="gate-card__value-row">
            <span class="gate-card__value">{{ row.value }}</span>
            <span class="gate-card__threshold" :title="row.threshold">
              <template v-if="splitThreshold(row.threshold).comparator">
                <span class="gate-card__cmp">{{ splitThreshold(row.threshold).comparator }}</span>
                <span>{{ splitThreshold(row.threshold).target }}</span>
              </template>
              <template v-else>{{ row.threshold }}</template>
            </span>
          </div>
          <div class="gate-card__footer">
            <span class="gate-card__more">Details ›</span>
          </div>
        </button>
      </div>

      <button
        type="button"
        class="gate-scorecard__nav gate-scorecard__nav--next"
        :disabled="selectedIndex >= rows.length - 1"
        aria-label="Next gate"
        @click="step(1)"
      >
        <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 6l6 6-6 6" />
        </svg>
      </button>
    </div>

    <ul class="gate-scorecard__dots" aria-hidden="true">
      <li
        v-for="(row, idx) in rows"
        :key="`dot-${row.name}`"
        class="dot-pip"
        :class="[`dot-pip--${row.status}`, { 'dot-pip--active': selectedIndex === idx }]"
        @click="selectIndex(idx)"
      />
    </ul>

    <p class="gate-scorecard__hint">
      Tap any card (or use arrow keys) to open its full detail in the
      <strong>Gate detail</strong> tab below.
    </p>
  </article>
</template>

<style scoped>
.gate-scorecard {
  padding: 18px 22px 20px;
}
.gate-scorecard__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.gate-scorecard__title h2 {
  margin: 0;
  font-size: clamp(1.05rem, 1.6vw, 1.35rem);
  letter-spacing: -0.03em;
}
.gate-scorecard__counts {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.gate-scorecard__count {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--ink);
}
.gate-scorecard__count .dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
}
.gate-scorecard__count--pass .dot { background: var(--teal); }
.gate-scorecard__count--prov .dot { background: var(--amber); }
.gate-scorecard__count--fail .dot { background: var(--red); }

.gate-scorecard__carousel {
  position: relative;
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) 36px;
  align-items: stretch;
  gap: 8px;
}
.gate-scorecard__nav {
  appearance: none;
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  align-self: center;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--surface-2);
  color: var(--ink);
  cursor: pointer;
  transition: background 140ms ease, color 140ms ease, transform 140ms ease;
}
.gate-scorecard__nav:hover:not(:disabled) {
  background: var(--maize-soft);
  color: var(--maize-ink);
  border-color: color-mix(in srgb, var(--maize) 40%, var(--line));
}
.gate-scorecard__nav:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.gate-scorecard__track {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(180px, 1fr);
  gap: 10px;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  padding: 2px 2px 10px;
  scrollbar-width: thin;
  scrollbar-color: color-mix(in srgb, var(--blue) 30%, transparent) transparent;
}
.gate-scorecard__track::-webkit-scrollbar {
  height: 6px;
}
.gate-scorecard__track::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--blue) 30%, transparent);
  border-radius: 999px;
}

.gate-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 13px;
  border-radius: 16px;
  border: 1px solid var(--line);
  background: var(--surface-2);
  color: var(--ink);
  text-align: left;
  cursor: pointer;
  scroll-snap-align: start;
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease, background 160ms ease;
  position: relative;
  min-width: 0;
}
.gate-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px color-mix(in srgb, var(--blue) 15%, transparent);
}
.gate-card--active {
  border-color: color-mix(in srgb, var(--blue) 55%, var(--line));
  box-shadow: 0 8px 22px color-mix(in srgb, var(--blue) 22%, transparent);
  background: color-mix(in srgb, var(--blue) 6%, var(--surface-2));
}
.gate-card--active::after {
  content: "";
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: -10px;
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--blue), var(--maize));
}

.gate-card--pass { border-top: 3px solid var(--teal); }
.gate-card--fail { border-top: 3px solid var(--red); }
.gate-card--provisional { border-top: 3px solid var(--amber); }

.gate-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.gate-card__conf {
  font-size: 0.7rem;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--blue-soft);
  color: var(--blue);
  letter-spacing: 0.04em;
  cursor: help;
}
.gate-card__name {
  font-size: 0.92rem;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: -0.01em;
  color: var(--ink);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.gate-card__value-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-top: 2px;
  flex-wrap: wrap;
}
.gate-card__value {
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
}
.gate-card__threshold {
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
  font-size: 0.78rem;
  color: var(--muted);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.gate-card__cmp {
  font-size: 0.9rem;
  color: var(--muted-2);
  margin-right: 1px;
}
.gate-card__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: auto;
  padding-top: 4px;
}
.gate-card__more {
  font-size: 0.74rem;
  color: var(--muted);
  font-weight: 600;
}
.gate-card--active .gate-card__more {
  color: var(--blue);
}

.gate-scorecard__dots {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
}
.dot-pip {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--line);
  cursor: pointer;
  transition: transform 140ms ease, background 140ms ease;
}
.dot-pip--pass { background: color-mix(in srgb, var(--teal) 60%, var(--line)); }
.dot-pip--provisional { background: color-mix(in srgb, var(--amber) 60%, var(--line)); }
.dot-pip--fail { background: color-mix(in srgb, var(--red) 60%, var(--line)); }
.dot-pip--active {
  transform: scale(1.35);
  outline: 2px solid color-mix(in srgb, var(--blue) 55%, transparent);
  outline-offset: 2px;
}

.gate-scorecard__hint {
  margin: 10px 0 0;
  font-size: 0.82rem;
  color: var(--muted);
  text-align: center;
}
.gate-scorecard__hint strong {
  color: var(--blue);
}

@media (max-width: 640px) {
  .gate-scorecard__track {
    grid-auto-columns: 80%;
  }
  .gate-scorecard__carousel {
    grid-template-columns: 28px minmax(0, 1fr) 28px;
  }
  .gate-scorecard__nav {
    width: 28px;
    height: 28px;
  }
}
</style>

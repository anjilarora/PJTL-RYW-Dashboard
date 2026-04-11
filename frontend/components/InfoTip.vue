<script setup lang="ts">
withDefaults(
  defineProps<{
    label?: string
    content: string
    placement?: "top" | "bottom" | "right" | "left"
  }>(),
  { label: "More information", placement: "bottom" }
)

const open = ref(false)
const rootEl = ref<HTMLElement | null>(null)

function toggle() {
  open.value = !open.value
}

function close() {
  open.value = false
}

function onDocClick(event: MouseEvent) {
  if (!open.value) return
  const target = event.target as Node
  if (rootEl.value && !rootEl.value.contains(target)) open.value = false
}

function onKey(event: KeyboardEvent) {
  if (event.key === "Escape" && open.value) open.value = false
}

onMounted(() => {
  document.addEventListener("click", onDocClick)
  document.addEventListener("keydown", onKey)
})
onBeforeUnmount(() => {
  document.removeEventListener("click", onDocClick)
  document.removeEventListener("keydown", onKey)
})
</script>

<template>
  <span ref="rootEl" class="info-tip" :class="{ 'info-tip--open': open }">
    <button
      type="button"
      class="info-tip__trigger"
      :aria-label="label"
      :aria-expanded="open"
      @click.stop="toggle"
      @blur="close"
    >
      <span aria-hidden="true">i</span>
    </button>
    <Transition name="info-tip-fade">
      <span
        v-if="open"
        class="info-tip__bubble"
        :class="`info-tip__bubble--${placement}`"
        role="tooltip"
      >
        {{ content }}
      </span>
    </Transition>
  </span>
</template>

<style scoped>
.info-tip {
  position: relative;
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.info-tip__trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1px solid var(--line-strong);
  background: var(--surface-2);
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 700;
  font-family: ui-serif, Georgia, serif;
  font-style: italic;
  cursor: pointer;
  padding: 0;
  transition: color 120ms ease, border-color 120ms ease, background 120ms ease;
}

.info-tip__trigger:hover,
.info-tip__trigger:focus-visible {
  color: var(--blue);
  border-color: var(--blue);
  background: var(--blue-soft);
  outline: none;
}

.info-tip--open .info-tip__trigger {
  color: var(--blue);
  border-color: var(--blue);
  background: var(--blue-soft);
}

.info-tip__bubble {
  position: absolute;
  z-index: 20;
  min-width: 220px;
  max-width: 320px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--surface);
  color: var(--ink);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  font-size: 0.85rem;
  line-height: 1.5;
  white-space: normal;
  text-align: left;
  font-weight: 400;
  font-style: normal;
  text-transform: none;
  letter-spacing: normal;
  font-family: inherit;
}

.info-tip__bubble--bottom {
  top: calc(100% + 8px);
  left: 0;
}

.info-tip__bubble--top {
  bottom: calc(100% + 8px);
  left: 0;
}

.info-tip__bubble--right {
  top: 50%;
  left: calc(100% + 10px);
  transform: translateY(-50%);
}

.info-tip__bubble--left {
  top: 50%;
  right: calc(100% + 10px);
  transform: translateY(-50%);
}

.info-tip-fade-enter-active,
.info-tip-fade-leave-active {
  transition: opacity 120ms ease, transform 120ms ease;
}
.info-tip-fade-enter-from,
.info-tip-fade-leave-to {
  opacity: 0;
  transform: translateY(-2px);
}
</style>

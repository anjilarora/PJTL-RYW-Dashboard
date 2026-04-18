<script setup lang="ts">
/**
 * Reusable upload drop-zone. Mirrors the reference UX: dashed box,
 * large centered upload icon, "Click to upload or drag and drop" headline,
 * and a subtle line listing the accepted file types.
 *
 * Emits a standard `change` event with the selected File (or null). Consumers
 * decide what to do next (parse JSON, POST multipart, etc.).
 */
interface Props {
  accept?: string
  acceptLabel?: string
  disabled?: boolean
  headline?: string
  hint?: string
  multiple?: boolean
  fileName?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  accept: "",
  acceptLabel: "",
  disabled: false,
  headline: "Click to upload or drag and drop",
  hint: "",
  multiple: false,
  fileName: ""
})

const emit = defineEmits<{ (e: "file-picked", file: File | null): void }>()

const inputEl = ref<HTMLInputElement | null>(null)
const dragging = ref(false)
const pickedName = ref<string>(props.fileName ?? "")

watch(() => props.fileName, (v) => { if (v !== undefined) pickedName.value = v ?? "" })

function openPicker() {
  if (props.disabled) return
  inputEl.value?.click()
}

function onChange(ev: Event) {
  const file = (ev.target as HTMLInputElement).files?.[0] ?? null
  if (file) pickedName.value = file.name
  emit("file-picked", file)
}

function onDrop(ev: DragEvent) {
  ev.preventDefault()
  dragging.value = false
  if (props.disabled) return
  const file = ev.dataTransfer?.files?.[0] ?? null
  if (file) {
    pickedName.value = file.name
    emit("file-picked", file)
  }
}
function onDragOver(ev: DragEvent) {
  ev.preventDefault()
  if (props.disabled) return
  dragging.value = true
}
function onDragLeave() {
  dragging.value = false
}
function onKey(ev: KeyboardEvent) {
  if (ev.key === "Enter" || ev.key === " ") {
    ev.preventDefault()
    openPicker()
  }
}
</script>

<template>
  <div
    class="dropzone"
    :class="{ 'dropzone--active': dragging, 'dropzone--disabled': disabled }"
    tabindex="0"
    role="button"
    :aria-label="headline"
    @click="openPicker"
    @keydown="onKey"
    @drop="onDrop"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
  >
    <input
      ref="inputEl"
      type="file"
      class="dropzone__input"
      :accept="accept"
      :disabled="disabled"
      :multiple="multiple"
      @change="onChange"
    />
    <span class="dropzone__icon" aria-hidden="true">
      <svg viewBox="0 0 48 48" width="36" height="36" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M24 32V10" />
        <path d="M14 20l10-10 10 10" />
        <path d="M8 34v4a2 2 0 0 0 2 2h28a2 2 0 0 0 2-2v-4" />
      </svg>
    </span>
    <span class="dropzone__headline">{{ headline }}</span>
    <span v-if="acceptLabel" class="dropzone__types">{{ acceptLabel }}</span>
    <span v-if="hint" class="dropzone__hint">{{ hint }}</span>
    <span v-if="pickedName" class="dropzone__picked" :title="pickedName">
      <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 4h10l6 6v10a2 2 0 0 1-2 2H4z" />
        <path d="M14 4v6h6" />
      </svg>
      {{ pickedName }}
    </span>
  </div>
</template>

<style scoped>
.dropzone {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 28px 20px;
  border: 1.5px dashed var(--line-strong);
  border-radius: 18px;
  background: var(--surface-2);
  color: var(--ink);
  text-align: center;
  cursor: pointer;
  transition: border-color 160ms ease, background 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}
.dropzone:hover,
.dropzone:focus-visible {
  outline: none;
  border-color: var(--blue);
  background: color-mix(in srgb, var(--blue) 5%, var(--surface-2));
  box-shadow: 0 0 0 3px var(--blue-soft);
}
.dropzone--active {
  border-color: var(--blue);
  background: var(--blue-soft);
  transform: translateY(-1px);
}
.dropzone--disabled {
  opacity: 0.55;
  cursor: not-allowed;
  pointer-events: none;
}
.dropzone__input {
  position: absolute;
  inset: 0;
  opacity: 0;
  pointer-events: none;
}
.dropzone__icon {
  display: inline-grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--line);
  color: var(--muted);
  margin-bottom: 4px;
}
.dropzone:hover .dropzone__icon,
.dropzone--active .dropzone__icon {
  color: var(--blue);
  border-color: var(--blue);
}
.dropzone__headline {
  font-size: 1rem;
  font-weight: 700;
  color: var(--ink);
}
.dropzone__types {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.dropzone__hint {
  font-size: 0.8rem;
  color: var(--muted);
  max-width: 44ch;
}
.dropzone__picked {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--line);
  font-size: 0.82rem;
  color: var(--ink);
  max-width: 90%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

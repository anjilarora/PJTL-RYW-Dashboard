export type ThemePreference = "light" | "dark" | "system"

const STORAGE_KEY = "ryw_theme"

function resolveEffective(pref: ThemePreference): "light" | "dark" {
  if (pref === "system" && import.meta.client) {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
  }
  if (pref === "light") return "light"
  return "dark"
}

export function useAppTheme() {
  const preference = useState<ThemePreference>("app-theme-pref", () => "system")

  function applyDom(effective: "light" | "dark") {
    if (!import.meta.client) return
    document.documentElement.dataset.theme = effective
    document.documentElement.style.colorScheme = effective
  }

  function setPreference(pref: ThemePreference) {
    preference.value = pref
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEY, pref)
      applyDom(resolveEffective(pref))
    }
  }

  function initFromStorage() {
    if (!import.meta.client) return
    const raw = localStorage.getItem(STORAGE_KEY) as ThemePreference | null
    if (raw === "light" || raw === "dark" || raw === "system") preference.value = raw
    applyDom(resolveEffective(preference.value))
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
      if (preference.value === "system") applyDom(resolveEffective("system"))
    })
  }

  return { preference, setPreference, initFromStorage, resolveEffective }
}

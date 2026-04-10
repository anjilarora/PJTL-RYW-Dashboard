import { useAppTheme } from "~/composables/useAppTheme"

export default defineNuxtPlugin(() => {
  const { initFromStorage } = useAppTheme()
  initFromStorage()
})

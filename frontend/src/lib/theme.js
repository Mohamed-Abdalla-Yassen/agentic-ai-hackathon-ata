const KEY = 'spacematch_theme'

export function getStoredTheme() {
  try {
    return localStorage.getItem(KEY)
  } catch {
    return null
  }
}

export function systemTheme() {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light'
}

export function resolveTheme() {
  return getStoredTheme() || systemTheme()
}

export function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme)
  document.documentElement.style.colorScheme = theme
  try {
    localStorage.setItem(KEY, theme)
  } catch {
    /* private mode — the theme just won't persist */
  }
}

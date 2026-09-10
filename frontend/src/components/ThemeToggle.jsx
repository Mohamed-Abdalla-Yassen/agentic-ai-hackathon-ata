import { useEffect, useState } from 'react'
import { IconButton } from './ui/primitives'
import { applyTheme, resolveTheme } from '../lib/theme'

export default function ThemeToggle() {
  const [theme, setTheme] = useState(resolveTheme)

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  const next = theme === 'dark' ? 'light' : 'dark'

  return (
    <IconButton
      icon={theme === 'dark' ? 'sun' : 'moon'}
      label={`Switch to ${next} mode`}
      onClick={() => setTheme(next)}
    />
  )
}

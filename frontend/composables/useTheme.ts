/**
 * Thème visuel de l'application.
 *
 * Le design system Carbon expose 4 thèmes ; l'application en utilise deux,
 * appliqués via une classe sur <html> :
 *   - `light` → `.cds--g10`  (fond gris clair, surfaces blanches)
 *   - `dark`  → `.cds--g100` (fond noir, surfaces grises)
 *
 * La préférence est stockée dans un cookie lisible au rendu serveur, ce qui
 * permet d'appliquer la bonne classe dès le HTML initial (aucun flash).
 */
export type ThemeName = 'light' | 'dark'

export const THEME_COOKIE = 'ecoloop_theme'

/** Classe Carbon correspondant à chaque thème. */
export const THEME_CLASSES: Record<ThemeName, string> = {
  light: 'cds--g10',
  dark: 'cds--g100'
}

export const useTheme = () => {
  const cookie = useCookie<ThemeName>(THEME_COOKIE, {
    maxAge: 60 * 60 * 24 * 365,
    sameSite: 'lax',
    default: () => 'light'
  })

  const theme = useState<ThemeName>('theme', () => (cookie.value === 'dark' ? 'dark' : 'light'))

  const isDark = computed(() => theme.value === 'dark')
  const themeClass = computed(() => THEME_CLASSES[theme.value])
  /** Libellé du thème vers lequel basculerait le bouton. */
  const nextThemeLabel = computed(() => (isDark.value ? 'Thème clair' : 'Thème sombre'))

  const setTheme = (value: ThemeName) => {
    theme.value = value
    cookie.value = value
  }

  const toggleTheme = () => setTheme(isDark.value ? 'light' : 'dark')

  return {
    theme,
    isDark,
    themeClass,
    nextThemeLabel,
    setTheme,
    toggleTheme
  }
}

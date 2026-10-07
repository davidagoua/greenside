/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './components/**/*.{js,vue,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './plugins/**/*.{js,ts}',
    './app.vue',
    './error.vue'
  ],
  theme: {
    extend: {
      colors: {
        /**
         * Design system Carbon (IBM).
         *
         * Ces utilitaires ne contiennent aucune couleur en dur : ils pointent vers
         * les variables CSS `--cds-*` définies par `@carbon/styles`. Le thème est
         * donc piloté par la classe appliquée sur <html> (`.cds--g10` en clair,
         * `.cds--g100` en sombre) — voir `composables/useTheme.ts`.
         *
         * Utilisation : `bg-cds-layer-01`, `text-cds-text-secondary`,
         * `border-cds-border-subtle`.
         *
         * Attention : les jetons Carbon sont des valeurs hex/rgba, pas des canaux
         * séparés — les modificateurs d'opacité Tailwind (`bg-cds-layer-01/50`)
         * ne s'appliquent donc PAS. Utiliser les jetons dédiés (overlay,
         * layer-hover-01, background-selected…) à la place.
         */
        cds: {
          background: 'var(--cds-background)',
          'background-hover': 'var(--cds-background-hover)',
          'background-active': 'var(--cds-background-active)',
          'background-selected': 'var(--cds-background-selected)',
          'background-selected-hover': 'var(--cds-background-selected-hover)',
          'background-inverse': 'var(--cds-background-inverse)',
          'background-brand': 'var(--cds-background-brand)',

          layer: 'var(--cds-layer)',
          'layer-01': 'var(--cds-layer-01)',
          'layer-02': 'var(--cds-layer-02)',
          'layer-03': 'var(--cds-layer-03)',
          'layer-hover-01': 'var(--cds-layer-hover-01)',
          'layer-hover-02': 'var(--cds-layer-hover-02)',
          'layer-active-01': 'var(--cds-layer-active-01)',
          'layer-selected-01': 'var(--cds-layer-selected-01)',
          'layer-selected-hover-01': 'var(--cds-layer-selected-hover-01)',
          'layer-accent-01': 'var(--cds-layer-accent-01)',
          'layer-accent-hover-01': 'var(--cds-layer-accent-hover-01)',

          field: 'var(--cds-field)',
          'field-01': 'var(--cds-field-01)',
          'field-02': 'var(--cds-field-02)',
          'field-hover-01': 'var(--cds-field-hover-01)',

          'border-subtle': 'var(--cds-border-subtle)',
          'border-subtle-01': 'var(--cds-border-subtle-01)',
          'border-subtle-selected-01': 'var(--cds-border-subtle-selected-01)',
          'border-strong': 'var(--cds-border-strong)',
          'border-strong-01': 'var(--cds-border-strong-01)',
          'border-inverse': 'var(--cds-border-inverse)',
          'border-interactive': 'var(--cds-border-interactive)',
          'border-disabled': 'var(--cds-border-disabled)',
          'border-tile': 'var(--cds-border-tile)',

          text: {
            primary: 'var(--cds-text-primary)',
            secondary: 'var(--cds-text-secondary)',
            placeholder: 'var(--cds-text-placeholder)',
            helper: 'var(--cds-text-helper)',
            error: 'var(--cds-text-error)',
            inverse: 'var(--cds-text-inverse)',
            'on-color': 'var(--cds-text-on-color)',
            disabled: 'var(--cds-text-disabled)'
          },

          icon: {
            primary: 'var(--cds-icon-primary)',
            secondary: 'var(--cds-icon-secondary)',
            'on-color': 'var(--cds-icon-on-color)',
            disabled: 'var(--cds-icon-disabled)',
            inverse: 'var(--cds-icon-inverse)'
          },

          link: {
            primary: 'var(--cds-link-primary)',
            'primary-hover': 'var(--cds-link-primary-hover)',
            secondary: 'var(--cds-link-secondary)',
            visited: 'var(--cds-link-visited)',
            inverse: 'var(--cds-link-inverse)'
          },

          interactive: 'var(--cds-interactive)',
          focus: 'var(--cds-focus)',
          'focus-inset': 'var(--cds-focus-inset)',
          highlight: 'var(--cds-highlight)',
          overlay: 'var(--cds-overlay)',

          'support-error': 'var(--cds-support-error)',
          'support-success': 'var(--cds-support-success)',
          'support-warning': 'var(--cds-support-warning)',
          'support-info': 'var(--cds-support-info)',
          'support-error-inverse': 'var(--cds-support-error-inverse)',
          'support-success-inverse': 'var(--cds-support-success-inverse)',
          'support-warning-inverse': 'var(--cds-support-warning-inverse)',
          'support-info-inverse': 'var(--cds-support-info-inverse)',

          'button-primary': 'var(--cds-button-primary)',
          'button-primary-hover': 'var(--cds-button-primary-hover)',
          'button-primary-active': 'var(--cds-button-primary-active)',
          'button-secondary': 'var(--cds-button-secondary)',
          'button-secondary-hover': 'var(--cds-button-secondary-hover)',
          'button-tertiary': 'var(--cds-button-tertiary)',
          'button-tertiary-hover': 'var(--cds-button-tertiary-hover)',
          'button-danger-primary': 'var(--cds-button-danger-primary)',
          'button-danger-secondary': 'var(--cds-button-danger-secondary)',
          'button-danger-hover': 'var(--cds-button-danger-hover)',
          'button-danger-active': 'var(--cds-button-danger-active)',
          'button-disabled': 'var(--cds-button-disabled)',

          danger: 'var(--cds-danger)',
          'danger-hover': 'var(--cds-danger-hover)',

          'skeleton-background': 'var(--cds-skeleton-background)',
          'skeleton-element': 'var(--cds-skeleton-element)'
        },

        /**
         * COMPATIBILITÉ — `slate` et `eco` ne sont plus des palettes de couleurs
         * mais des alias vers les jetons Carbon. L'objectif est qu'aucune classe
         * oubliée lors de la migration n'introduise une couleur en dur (et donc
         * un rendu cassé en thème clair).
         *
         * Tout nouveau code doit utiliser les utilitaires `cds-*` ci-dessus.
         */
        slate: {
          50: 'var(--cds-text-primary)',
          100: 'var(--cds-text-primary)',
          200: 'var(--cds-text-primary)',
          300: 'var(--cds-text-secondary)',
          400: 'var(--cds-text-secondary)',
          500: 'var(--cds-text-helper)',
          600: 'var(--cds-text-placeholder)',
          700: 'var(--cds-border-strong)',
          800: 'var(--cds-border-subtle)',
          850: 'var(--cds-layer-hover-01)',
          900: 'var(--cds-layer-01)',
          950: 'var(--cds-background)'
        },

        eco: {
          300: 'var(--cds-link-primary)',
          400: 'var(--cds-link-primary)',
          500: 'var(--cds-button-primary-hover)',
          600: 'var(--cds-button-primary)',
          700: 'var(--cds-button-primary-active)',
          800: 'var(--cds-button-primary-active)',
          900: 'var(--cds-background-brand)',
          950: 'var(--cds-highlight)'
        }
      },

      fontFamily: {
        // Plex est la fonte du design system Carbon
        sans: [
          "'IBM Plex Sans'",
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif'
        ],
        mono: ["'IBM Plex Mono'", 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace']
      }
    }
  },
  plugins: []
}

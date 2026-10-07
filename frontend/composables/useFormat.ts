import type { Numeric } from '~/types'

/**
 * Formatage sûr des valeurs numériques renvoyées par l'API.
 *
 * Le backend sérialise les `NUMERIC` PostgreSQL en **chaîne** (« 1500.00 ») :
 * appeler `.toLocaleString()` sur ces valeurs ne produit aucun séparateur de
 * milliers (`String.prototype.toLocaleString` renvoie la chaîne telle quelle).
 * Ces helpers normalisent donc d'abord en nombre, puis formatent en fr-FR.
 */

/** Convertit une valeur API (nombre, chaîne décimale, vide) en nombre fini. */
export const toNumber = (value: Numeric | null | undefined): number | null => {
  if (value === null || value === undefined || value === '') return null
  if (typeof value === 'number') return Number.isFinite(value) ? value : null
  // Tolère les séparateurs d'espace et la virgule décimale française
  const normalized = Number(String(value).replace(/[\s\u00a0]/g, '').replace(',', '.'))
  return Number.isFinite(normalized) ? normalized : null
}

const withFraction = (digits: number) =>
  new Intl.NumberFormat('fr-FR', {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits
  })

export const useFormat = () => {
  /** Nombre formaté fr-FR, ou « — » si absent/invalide. */
  const formatNumber = (value: Numeric | null | undefined, digits = 0): string => {
    const n = toNumber(value)
    if (n === null) return '—'
    return withFraction(digits).format(n)
  }

  /** Montant + devise (ex. « 75 000 FCFA »). */
  const formatMoney = (value: Numeric | null | undefined, currency = 'FCFA'): string => {
    const n = toNumber(value)
    if (n === null) return '—'
    return `${withFraction(2).format(n)} ${currency}`
  }

  /** Quantité + unité (ex. « 432,5 kg »). */
  const formatQuantity = (value: Numeric | null | undefined, unit = 'kg'): string => {
    const n = toNumber(value)
    if (n === null) return '—'
    return `${withFraction(2).format(n)} ${unit}`
  }

  /** Évitement carbone (ex. « 648,75 kg CO₂e »). */
  const formatCo2 = (value: Numeric | null | undefined): string => {
    const n = toNumber(value)
    if (n === null) return '—'
    return `${withFraction(2).format(n)} kg CO₂e`
  }

  const formatDate = (value?: string | null): string => {
    if (!value) return '—'
    const d = new Date(value)
    if (Number.isNaN(d.getTime())) return '—'
    return new Intl.DateTimeFormat('fr-FR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    }).format(d)
  }

  const formatDateTime = (value?: string | null): string => {
    if (!value) return '—'
    const d = new Date(value)
    if (Number.isNaN(d.getTime())) return '—'
    return new Intl.DateTimeFormat('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(d)
  }

  /** Extrait un message d'erreur exploitable d'une erreur $fetch. */
  const errorMessage = (err: unknown, fallback = 'Une erreur est survenue'): string => {
    const detail = (err as { response?: { _data?: { detail?: unknown } } })?.response?._data?.detail
    if (typeof detail === 'string' && detail) return detail
    if (err instanceof Error && err.message) return err.message
    return fallback
  }

  return {
    toNumber,
    formatNumber,
    formatMoney,
    formatQuantity,
    formatCo2,
    formatDate,
    formatDateTime,
    errorMessage
  }
}

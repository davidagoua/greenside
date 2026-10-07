/**
 * Libellés et styles partagés pour les énumérations du backend
 * (`user_role`, `listing_status`, `transaction_status`).
 *
 * Les helpers `*BadgeClass` renvoient uniquement la **variante de couleur** d'une
 * étiquette Carbon ; la classe de base `cds--tag` est posée dans le gabarit :
 *
 *   <span class="cds--tag" :class="transactionStatusBadgeClass(tx.status)">
 */

export const ROLE_LABELS: Record<string, string> = {
  producer: 'Producteur',
  collector: 'Collecteur',
  admin: 'Administrateur'
}

export const ROLE_BADGE_CLASSES: Record<string, string> = {
  producer: 'cds--tag--blue',
  collector: 'cds--tag--cyan',
  admin: 'cds--tag--purple'
}

export const LISTING_STATUS_LABELS: Record<string, string> = {
  draft: 'Brouillon',
  published: 'Publiée',
  reserved: 'Réservée',
  in_transit: 'En transit',
  completed: 'Clôturée',
  cancelled: 'Annulée'
}

export const LISTING_STATUS_BADGE_CLASSES: Record<string, string> = {
  draft: 'cds--tag--gray',
  published: 'cds--tag--green',
  reserved: 'cds--tag--warm-gray',
  in_transit: 'cds--tag--cyan',
  completed: 'cds--tag--blue',
  cancelled: 'cds--tag--red'
}

export const TRANSACTION_STATUS_LABELS: Record<string, string> = {
  pending_escrow: 'En attente de séquestre',
  escrow_locked: 'Fonds sous séquestre',
  collected_pending_verification: 'Pesée en attente de validation',
  paid: 'Clôturé & Payé',
  disputed: 'Litige ouvert',
  cancelled: 'Annulé'
}

export const TRANSACTION_STATUS_BADGE_CLASSES: Record<string, string> = {
  pending_escrow: 'cds--tag--gray',
  escrow_locked: 'cds--tag--warm-gray',
  collected_pending_verification: 'cds--tag--cyan',
  paid: 'cds--tag--green',
  disputed: 'cds--tag--red',
  cancelled: 'cds--tag--gray'
}

export const UNIT_LABELS: Record<string, string> = {
  kg: 'kg',
  tonne: 'tonne',
  litre: 'litre'
}

/** Statuts de transaction dans l'ordre du cycle de vie métier. */
export const TRANSACTION_STATUSES = [
  'pending_escrow',
  'escrow_locked',
  'collected_pending_verification',
  'paid',
  'disputed',
  'cancelled'
] as const

export const roleLabel = (role?: string | null): string =>
  (role && ROLE_LABELS[role]) || role || '—'

export const roleBadgeClass = (role?: string | null): string =>
  (role && ROLE_BADGE_CLASSES[role]) || 'bg-slate-800 text-slate-300'

export const listingStatusLabel = (status?: string | null): string =>
  (status && LISTING_STATUS_LABELS[status]) || status || '—'

export const listingStatusBadgeClass = (status?: string | null): string =>
  (status && LISTING_STATUS_BADGE_CLASSES[status]) || 'bg-slate-800 text-slate-300'

export const transactionStatusLabel = (status?: string | null): string =>
  (status && TRANSACTION_STATUS_LABELS[status]) || status || '—'

export const transactionStatusBadgeClass = (status?: string | null): string =>
  (status && TRANSACTION_STATUS_BADGE_CLASSES[status]) || 'bg-slate-800 text-slate-300'

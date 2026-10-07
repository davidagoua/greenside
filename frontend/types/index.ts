/**
 * Les champs `NUMERIC` PostgreSQL sont sérialisés en **chaîne** par Pydantic v2
 * (ex. `"1500.00"`), pas en nombre. Les agrégats analytics (`COUNT`) restent des
 * entiers. Utiliser `useFormat()` pour tout affichage.
 */
export type Numeric = number | string

export interface User {
  id: string
  email: string
  role: 'producer' | 'collector' | 'admin'
  organization_name: string | null
  phone: string
  is_active: boolean
  created_at: string
}

export interface WasteCategory {
  id: string
  slug: string
  name: string
  unit: string
  co2_factor_per_unit: number
  suggested_price_per_unit: number
}

export interface Location {
  id: string
  label: string | null
  address_text: string
  lat: number
  lng: number
  created_at: string
}

export interface Listing {
  id: string
  producer_id: string
  category_id: string
  category_slug: string
  category_name: string
  unit: string
  location_id: string
  location_label: string | null
  address_text: string
  lat: number
  lng: number
  title: string
  description: string | null
  estimated_quantity: number
  price_per_unit: number
  is_free_donation: boolean
  pickup_availability: {
    days: string[]
    hours?: string
  } | null
  images_urls: string[]
  status: 'draft' | 'published' | 'reserved' | 'in_transit' | 'completed' | 'cancelled'
  producer_organization: string | null
  created_at: string
  updated_at: string
}

export interface NearbyListing {
  id: string
  title: string
  estimated_quantity: number
  price_per_unit: number
  is_free_donation: boolean
  category_name: string
  category_slug: string
  unit: string
  distance_km: number
  lat: number
  lng: number
  address_text: string
  thumbnail_url: string | null
}

export interface Transaction {
  id: string
  listing_id: string
  listing_title: string
  listing_status: string
  category_name: string
  unit: string
  producer_id: string
  producer_organization: string | null
  producer_phone: string | null
  collector_id: string
  collector_organization: string | null
  collector_phone: string | null
  address_text: string
  lat: number
  lng: number
  agreed_quantity: number | null
  final_weight: number | null
  unit_price: number | null
  total_amount: number | null
  payment_status: 'pending_escrow' | 'escrow_locked' | 'collected_pending_verification' | 'paid' | 'disputed' | 'cancelled'
  escrow_reference: string | null
  collected_at: string | null
  qr_scanned_at: string | null
  co2_saved_total: number | null
  weighing_proof_url: string | null
  collector_confirmed_at: string | null
  producer_confirmed_at: string | null
  bsdd_number: string | null
  dispute_reason: string | null
  resolution_note: string | null
  created_at: string
  updated_at: string | null
  viewer_role: 'producer' | 'collector' | 'admin' | null
}

export interface ImpactData {
  total_quantity_kg: number
  total_co2_saved_kg: number
  total_financial_volume: number
  completed_transactions: number
  trees_equivalent: number
  by_material: Array<{
    category_slug: string
    category_name: string
    unit: string
    total_quantity: number
    co2_saved: number
    financial_volume: number
    transactions_count: number
  }>
  monthly: Array<{
    month: string
    quantity_kg: number
    co2_saved_kg: number
    financial_volume: number
  }>
}

/** Réponse de `GET /analytics/global` (réservé au rôle `admin`). */
export interface GlobalStats {
  total_quantity_kg: Numeric
  total_co2_saved_kg: Numeric
  total_financial_volume: Numeric
  completed_transactions: number
  trees_equivalent: Numeric
  by_material: Array<{
    category_slug: string
    category_name: string
    unit: string
    total_quantity: Numeric
    co2_saved: Numeric
    financial_volume: Numeric
    transactions_count: number
  }>
  monthly: Array<{
    month: string
    quantity_kg: number
    co2_saved_kg: number
    financial_volume: number
  }>
  users_by_role: Record<string, number>
  listings_by_status: Record<string, number>
  open_disputes: number
}

/** Payload de `POST /categories` (admin). */
export interface CategoryInput {
  slug: string
  name: string
  unit: 'kg' | 'tonne' | 'litre'
  co2_factor_per_unit: number
  suggested_price_per_unit: number
}

/** Payload de `PATCH /categories/{id}` (admin). */
export type CategoryUpdate = Partial<Omit<CategoryInput, 'slug'>>

/** Payload de `POST /admin/transactions/{id}/resolve`. */
export interface ResolveDisputeInput {
  resolution: 'paid' | 'cancelled'
  note?: string | null
}

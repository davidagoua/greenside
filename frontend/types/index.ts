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

// Shared TypeScript types matching backend models

export type ShipmentStatus = 'pending' | 'in_transit' | 'customs' | 'delayed' | 'delivered' | 'cancelled'
export type ShipmentMode = 'air' | 'sea' | 'road' | 'rail' | 'multimodal'
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'
export type NotificationType = 'eta_conflict' | 'delay_risk' | 'status_change' | 'stale_update' | 'system'

export interface User {
  id: number
  email: string
  username: string
  full_name: string | null
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export interface TrackingEvent {
  id: number
  shipment_id: number
  event_time: string
  location: string | null
  status: ShipmentStatus
  description: string | null
  is_simulated: boolean
  created_at: string
}

export interface Shipment {
  id: number
  tracking_number: string
  title: string
  description: string | null
  origin_location: string
  destination_location: string
  origin_country: string | null
  destination_country: string | null
  carrier: string | null
  mode: ShipmentMode
  status: ShipmentStatus
  eta: string | null
  etd: string | null
  actual_delivery: string | null
  risk_level: RiskLevel
  risk_score: number
  risk_factors: string | null  // JSON string
  has_eta_conflict: boolean
  eta_conflict_reason: string | null
  last_update_at: string
  is_stale: boolean
  weight_kg: number | null
  value_usd: number | null
  owner_id: number
  created_at: string
  updated_at: string
  tracking_events?: TrackingEvent[]
}

export interface ShipmentListItem {
  id: number
  tracking_number: string
  title: string
  origin_location: string
  destination_location: string
  carrier: string | null
  mode: ShipmentMode
  status: ShipmentStatus
  eta: string | null
  risk_level: RiskLevel
  risk_score: number
  has_eta_conflict: boolean
  is_stale: boolean
  owner_id: number
  created_at: string
  updated_at: string
}

export interface PaginatedShipments {
  items: ShipmentListItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface Notification {
  id: number
  user_id: number
  shipment_id: number | null
  type: NotificationType
  title: string
  message: string
  is_read: boolean
  created_at: string
}

export interface DashboardStats {
  total_shipments: number
  in_transit: number
  delivered: number
  delayed: number
  pending: number
  cancelled: number
  high_risk_count: number
  eta_conflict_count: number
  stale_count: number
  avg_risk_score: number
  on_time_rate: number
  by_mode: Record<string, number>
  by_status: Record<string, number>
  by_risk: Record<string, number>
  recent_shipments_7d: number
}

export interface AuthToken {
  access_token: string
  token_type: string
  user: User
}

export interface ShipmentFilters {
  search?: string
  status?: ShipmentStatus | ''
  mode?: ShipmentMode | ''
  risk_level?: RiskLevel | ''
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

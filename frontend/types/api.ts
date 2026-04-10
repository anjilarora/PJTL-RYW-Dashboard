export type Role = "analyst" | "ops" | "admin"

export interface ApiEnvelope<T> {
  success: boolean
  data: T
  error?: {
    code: string
    message: string
    details?: Record<string, unknown>
  }
}

export interface Booking {
  id: string
  rider_name: string
  pickup: string
  dropoff: string
  mode: string
  status: string
  created_at: string
}

export interface DispatchAssignment {
  id: string
  booking_id: string
  driver_id: string
  vehicle_id: string
  status: string
  created_at: string
}

export interface Payment {
  id: string
  booking_id: string
  amount: number
  currency: string
  status: string
  created_at: string
}

export interface Profile {
  id: string
  name: string
  email: string
  organization: string
  role: Role
  notification_opt_in: boolean
}

export interface NotificationEvent {
  id: string
  channel: string
  recipient: string
  message: string
  status: string
  created_at: string
}

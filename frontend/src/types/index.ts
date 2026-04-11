export type UserRole = 'volunteer' | 'community_admin' | 'system_admin'

export interface User {
  id: number
  username: string
  real_name?: string | null
  gender?: 'male' | 'female' | null
  phone?: string | null
  age?: number | null
  avatar?: string
  role: UserRole
  community?: number | null
  community_name?: string
  skills?: string
  total_service_hours?: number
  is_active?: boolean
  approval_status?: 'pending' | 'approved' | 'rejected'
  approval_note?: string
  profile_completed?: boolean
  date_joined?: string
}

export interface Community {
  id: number
  name: string
  description?: string
  cover_image?: string
  created_at?: string
}

export type ActivityStatus = 'pending' | 'approved' | 'rejected' | 'ongoing' | 'finished'

export interface Activity {
  id: number
  title: string
  type: string
  type_display?: string
  other_type?: string | null
  location: string
  start_time: string
  end_time: string
  max_volunteers: number
  community: number
  community_name?: string
  description: string
  deadline: string
  status: ActivityStatus
  allow_external: boolean
  cover_image?: string
  created_by: number
  created_by_name?: string
  reviewer?: number | null
  reviewer_name?: string
  review_note?: string
  reviewed_at?: string | null
  approved_count?: number
  created_at: string
  updated_at?: string
}

export interface ActivityType {
  id: number
  name: string
  sort_order: number
  is_active: boolean
  description?: string | null
  created_at?: string
}

export type RegistrationStatus = 'pending' | 'approved' | 'rejected' | 'canceled'

export interface Registration {
  id: number
  activity: number
  activity_title?: string
  activity_status?: ActivityStatus
  volunteer: number
  volunteer_name?: string
  community_name?: string
  status: RegistrationStatus
  apply_time: string
  reviewed_by?: number | null
  reviewed_by_name?: string
  review_note?: string
  reviewed_at?: string | null
  attendance_status?: 'pending' | 'confirmed' | 'rejected'
}

export interface Attendance {
  id: number
  registration: number
  volunteer?: number
  volunteer_name?: string
  activity?: number
  activity_title?: string
  community?: number
  community_name?: string
  check_in_time?: string | null
  check_out_time?: string | null
  hours?: number | null
  approved_hours?: number | null
  status: 'pending' | 'confirmed' | 'rejected'
  reviewed_by?: number | null
  reviewed_by_name?: string
  review_note?: string
  reviewed_at?: string | null
}

export interface Notice {
  id: number
  title: string
  content: string
  community?: number | null
  community_name?: string
  publish_time: string
  created_by: number
  created_by_name?: string
}

export interface Evaluation {
  id: number
  activity: number
  activity_title?: string
  volunteer: number
  volunteer_name?: string
  rating: number
  comment?: string
  created_at: string
}

export interface ActivityComment {
  id: number
  activity: number
  author: number
  author_name: string
  author_username?: string
  author_role?: UserRole
  author_avatar?: string | null
  parent?: number | null
  parent_author_name?: string | null
  content: string
  is_deleted: boolean
  can_delete: boolean
  created_at: string
  updated_at?: string
}

export interface OverviewStats {
  role: UserRole
  total_users?: number
  total_activities?: number
  pending_activity_reviews?: number
  pending_registration_reviews?: number
  pending_attendance_reviews?: number
  confirmed_hours?: number
  approved_registrations?: number
  pending_registrations?: number
  attended_activities?: number
}

export interface ServiceRankingItem {
  volunteer_id: number
  volunteer_name: string
  community_name?: string
  total_hours: number
  activity_count: number
}

export interface CommunityDistributionItem {
  community_id: number
  community_name: string
  total_hours: number
  participant_count: number
}

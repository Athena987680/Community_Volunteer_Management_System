// 用户角色枚举：用于路由守卫、页面显示和接口权限分支。
export type UserRole = 'volunteer' | 'community_admin' | 'system_admin'

// 用户资料与账号状态模型。
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

// 社区基础信息模型。
export interface Community {
  id: number
  name: string
  description?: string
  cover_image?: string
  created_at?: string
}

// 社区变更审核状态。
export type CommunityChangeStatus = 'pending' | 'approved' | 'rejected'

// 社区变更申请模型。
export interface CommunityChangeRequest {
  id: number
  applicant: number
  applicant_name?: string
  applicant_username?: string
  from_community?: number | null
  from_community_name?: string | null
  to_community: number
  to_community_name?: string
  status: CommunityChangeStatus
  reason?: string | null
  review_note?: string | null
  reviewed_by?: number | null
  reviewed_by_name?: string
  applied_at: string
  reviewed_at?: string | null
}

// 活动生命周期状态（业务运行态）。
export type ActivityStatus = 'unopened' | 'recruiting' | 'upcoming' | 'ongoing' | 'finished'
// 活动审核状态（审批态）。
export type ActivityReviewStatus = 'pending' | 'approved' | 'rejected'

// 活动详情模型。
export interface Activity {
  id: number
  title: string
  type?: string
  activity_type?: number | null
  activity_type_name?: string
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
  review_status: ActivityReviewStatus
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

// 活动类型字典模型。
export interface ActivityType {
  id: number
  name: string
  sort_order: number
  is_active: boolean
  description?: string | null
  created_at?: string
}

// 报名审核状态。
export type RegistrationStatus = 'pending' | 'approved' | 'rejected' | 'canceled'

// 报名记录模型。
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

// 签到、签退与工时审核模型。
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

// 公告模型。
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

// 活动评价模型。
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

// 活动评论模型（支持回复与软删除）。
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

// 管理员操作审计日志模型。
export interface OperationLog {
  id: number
  operator?: number | null
  operator_display?: string | null
  operator_name?: string | null
  module: string
  action: string
  method: string
  path: string
  target_type?: string | null
  target_id?: number | null
  target_display?: string | null
  status: 'success' | 'failed'
  status_code: number
  ip_address?: string | null
  detail?: string | null
  created_at: string
}

// 仪表盘概览统计模型。
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

// 志愿者服务时长排行项模型。
export interface ServiceRankingItem {
  volunteer_id: number
  volunteer_name: string
  community_name?: string
  total_hours: number
  activity_count: number
}

// 社区服务时长分布项模型。
export interface CommunityDistributionItem {
  community_id: number
  community_name: string
  total_hours: number
  participant_count: number
}


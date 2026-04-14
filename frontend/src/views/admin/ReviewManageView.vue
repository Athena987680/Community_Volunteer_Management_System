<template>
  <div class="view-page">
    <h2 class="page-title">审核管理</h2>
    <el-card>
      <el-tabs v-model="activeTab">
        <el-tab-pane v-if="userStore.isAdmin" name="admin-account">
          <template #label>社区管理员注册审核</template>
          <div class="card-header" style="margin-bottom: 12px">
            <el-radio-group v-model="adminAccountFilter" size="small">
              <el-radio-button label="pending">待审核</el-radio-button>
              <el-radio-button label="reviewed">已审核</el-radio-button>
              <el-radio-button label="all">全部</el-radio-button>
            </el-radio-group>
          </div>
          <el-table :data="filteredCommunityAdmins" border>
            <el-table-column prop="username" label="用户名" width="140" />
            <el-table-column prop="real_name" label="姓名" width="120" />
            <el-table-column prop="community_name" label="社区" width="150" />
            <el-table-column prop="phone" label="手机号" width="150" />
            <el-table-column label="审核状态" width="120">
              <template #default="{ row }">
                <el-tag :type="adminApprovalType(row.approval_status)">{{ adminApprovalText(row.approval_status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="申请时间" width="180">
              <template #default="{ row }">{{ fmt(row.date_joined) }}</template>
            </el-table-column>
            <el-table-column prop="approval_note" label="备注" min-width="200" />
            <el-table-column label="操作" :width="isMobile ? 88 : 180" :fixed="isMobile ? undefined : 'right'">
              <template #default="{ row }">
                <template v-if="!isMobile">
                  <el-button v-if="row.approval_status === 'pending'" link type="success" @click="approveCommunityAdmin(row.id)">
                    通过
                  </el-button>
                  <el-button v-if="row.approval_status === 'pending'" link type="danger" @click="rejectCommunityAdmin(row.id)">
                    拒绝
                  </el-button>
                </template>
                <template v-else>
                  <el-dropdown
                    v-if="row.approval_status === 'pending'"
                    trigger="click"
                    @command="(command: string) => handleAdminAccountCommand(row, command)"
                  >
                    <el-button link type="primary">
                      操作
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="approve">通过</el-dropdown-item>
                        <el-dropdown-item command="reject">拒绝</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                  <span v-else>-</span>
                </template>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane v-if="userStore.isAdmin" name="activity">
          <template #label>活动审核</template>
          <div class="card-header" style="margin-bottom: 12px">
            <el-radio-group v-model="activityFilter" size="small">
              <el-radio-button label="pending">待审核</el-radio-button>
              <el-radio-button label="reviewed">已审核</el-radio-button>
              <el-radio-button label="all">全部</el-radio-button>
            </el-radio-group>
          </div>
          <el-table :data="filteredActivities" border>
            <el-table-column prop="title" label="活动名称" min-width="180" />
            <el-table-column label="活动类型" width="140">
              <template #default="{ row }">{{ row.type_display || row.type }}</template>
            </el-table-column>
            <el-table-column prop="community_name" label="社区" width="140" />
            <el-table-column prop="created_by_name" label="发布人" width="120" />
            <el-table-column label="发布时间" width="180">
              <template #default="{ row }">{{ fmt(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="审核状态" width="110">
              <template #default="{ row }">
                <el-tag :type="activityReviewStatusType(row.review_status)">{{ activityReviewStatusText(row.review_status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="活动状态" width="110">
              <template #default="{ row }">
                <el-tag :type="activityStatusType(row.status)">{{ activityStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="review_note" label="审核备注" min-width="180" />
            <el-table-column label="审核时间" width="180">
              <template #default="{ row }">{{ fmt(row.reviewed_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" :width="isMobile ? 88 : 180" :fixed="isMobile ? undefined : 'right'">
              <template #default="{ row }">
                <template v-if="!isMobile">
                  <el-button v-if="row.review_status === 'pending'" link type="success" @click="reviewActivity(row.id, 'approved')">
                    通过
                  </el-button>
                  <el-button v-if="row.review_status === 'pending'" link type="danger" @click="reviewActivity(row.id, 'rejected')">
                    拒绝
                  </el-button>
                </template>
                <template v-else>
                  <el-dropdown v-if="row.review_status === 'pending'" trigger="click" @command="(command: string) => handleActivityCommand(row, command)">
                    <el-button link type="primary">
                      操作
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="approved">通过</el-dropdown-item>
                        <el-dropdown-item command="rejected">拒绝</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                  <span v-else>-</span>
                </template>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane v-if="userStore.isAdmin" name="community-change">
          <template #label>社区变更审核</template>
          <div class="card-header" style="margin-bottom: 12px">
            <el-radio-group v-model="communityChangeFilter" size="small">
              <el-radio-button label="pending">待审核</el-radio-button>
              <el-radio-button label="reviewed">已审核</el-radio-button>
              <el-radio-button label="all">全部</el-radio-button>
            </el-radio-group>
          </div>
          <el-table :data="filteredCommunityChanges" border>
            <el-table-column prop="applicant_name" label="志愿者" width="120">
              <template #default="{ row }">{{ row.applicant_name || row.applicant_username || '-' }}</template>
            </el-table-column>
            <el-table-column prop="from_community_name" label="原社区" width="140" />
            <el-table-column prop="to_community_name" label="目标社区" width="140" />
            <el-table-column prop="reason" label="申请原因" min-width="180" />
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="communityChangeStatusType(row.status)">{{ communityChangeStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="申请时间" width="180">
              <template #default="{ row }">{{ fmt(row.applied_at) }}</template>
            </el-table-column>
            <el-table-column prop="review_note" label="审核备注" min-width="180" />
            <el-table-column label="审核时间" width="180">
              <template #default="{ row }">{{ fmt(row.reviewed_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" :width="isMobile ? 88 : 180" :fixed="isMobile ? undefined : 'right'">
              <template #default="{ row }">
                <template v-if="!isMobile">
                  <el-button v-if="row.status === 'pending'" link type="success" @click="reviewCommunityChange(row.id, 'approved')">
                    通过
                  </el-button>
                  <el-button v-if="row.status === 'pending'" link type="danger" @click="reviewCommunityChange(row.id, 'rejected')">
                    拒绝
                  </el-button>
                </template>
                <template v-else>
                  <el-dropdown
                    v-if="row.status === 'pending'"
                    trigger="click"
                    @command="(command: string) => handleCommunityChangeCommand(row, command)"
                  >
                    <el-button link type="primary">
                      操作
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="approved">通过</el-dropdown-item>
                        <el-dropdown-item command="rejected">拒绝</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                  <span v-else>-</span>
                </template>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane name="registration">
          <template #label>报名审核</template>
          <div class="card-header" style="margin-bottom: 12px">
            <el-radio-group v-model="registrationFilter" size="small">
              <el-radio-button label="pending">待审核</el-radio-button>
              <el-radio-button label="reviewed">已审核</el-radio-button>
              <el-radio-button label="all">全部</el-radio-button>
            </el-radio-group>
          </div>
          <el-table :data="filteredRegistrations" border>
            <el-table-column prop="activity_title" label="活动名称" min-width="200" />
            <el-table-column prop="community_name" label="社区" width="140" />
            <el-table-column label="志愿者" width="120">
              <template #default="{ row }">
                <el-button link type="primary" @click="openVolunteerProfile(row)">{{ row.volunteer_name || '-' }}</el-button>
              </template>
            </el-table-column>
            <el-table-column label="报名时间" width="180">
              <template #default="{ row }">{{ fmt(row.apply_time) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="registrationStatusType(row.status)">{{ registrationStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="review_note" label="审核备注" min-width="180" />
            <el-table-column label="操作" :width="isMobile ? 88 : 180" :fixed="isMobile ? undefined : 'right'">
              <template #default="{ row }">
                <template v-if="!isMobile">
                  <el-button v-if="row.status === 'pending'" link type="success" @click="reviewRegistration(row.id, 'approve')">
                    通过
                  </el-button>
                  <el-button v-if="row.status === 'pending'" link type="danger" @click="reviewRegistration(row.id, 'reject')">
                    拒绝
                  </el-button>
                </template>
                <template v-else>
                  <el-dropdown
                    v-if="row.status === 'pending'"
                    trigger="click"
                    @command="(command: string) => handleRegistrationCommand(row, command)"
                  >
                    <el-button link type="primary">
                      操作
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="approve">通过</el-dropdown-item>
                        <el-dropdown-item command="reject">拒绝</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                  <span v-else>-</span>
                </template>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane name="attendance">
          <template #label>工时审核</template>
          <div class="card-header" style="margin-bottom: 12px">
            <el-radio-group v-model="attendanceFilter" size="small">
              <el-radio-button label="pending">待审核</el-radio-button>
              <el-radio-button label="reviewed">已审核</el-radio-button>
              <el-radio-button label="all">全部</el-radio-button>
            </el-radio-group>
          </div>
          <el-table :data="filteredAttendances" border>
            <el-table-column prop="activity_title" label="活动" min-width="180" />
            <el-table-column prop="volunteer_name" label="志愿者" width="120" />
            <el-table-column prop="community_name" label="社区" width="140" />
            <el-table-column label="签到" width="170">
              <template #default="{ row }">{{ fmt(row.check_in_time) }}</template>
            </el-table-column>
            <el-table-column label="签退" width="170">
              <template #default="{ row }">{{ fmt(row.check_out_time) }}</template>
            </el-table-column>
            <el-table-column prop="hours" label="原始工时" width="100" />
            <el-table-column prop="approved_hours" label="确认工时" width="100" />
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="attendanceStatusType(row.status)">{{ attendanceStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="review_note" label="审核备注" min-width="180" />
            <el-table-column label="操作" :width="isMobile ? 88 : 210" :fixed="isMobile ? undefined : 'right'">
              <template #default="{ row }">
                <template v-if="!isMobile">
                  <el-button
                    v-if="row.status === 'pending' && row.check_out_time"
                    link
                    type="success"
                    @click="confirmHours(row.id, row.hours || 0)"
                  >
                    确认工时
                  </el-button>
                  <el-button
                    v-if="row.status === 'pending' && row.check_out_time"
                    link
                    type="danger"
                    @click="rejectHours(row.id)"
                  >
                    驳回
                  </el-button>
                </template>
                <template v-else>
                  <el-dropdown
                    v-if="row.status === 'pending' && row.check_out_time"
                    trigger="click"
                    @command="(command: string) => handleAttendanceCommand(row, command)"
                  >
                    <el-button link type="primary">
                      操作
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="confirm">确认工时</el-dropdown-item>
                        <el-dropdown-item command="reject">驳回</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                  <span v-else>-</span>
                </template>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="profileVisible" title="志愿者个人主页" width="560px">
      <div v-loading="profileLoading">
        <template v-if="volunteerProfile">
          <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 14px">
            <el-avatar :size="64" :src="volunteerProfile.avatar">{{ volunteerProfile.real_name?.slice(0, 1) || 'V' }}</el-avatar>
            <div>
              <div style="font-size: 18px; font-weight: 700; color: #25384d">
                {{ volunteerProfile.real_name || volunteerProfile.username }}
              </div>
              <div class="meta-row">{{ volunteerProfile.community_name || '-' }}</div>
            </div>
          </div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户名">{{ volunteerProfile.username }}</el-descriptions-item>
            <el-descriptions-item label="姓名">{{ volunteerProfile.real_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="性别">{{ volunteerProfile.gender === 'female' ? '女' : volunteerProfile.gender === 'male' ? '男' : '-' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ volunteerProfile.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="年龄">{{ volunteerProfile.age || '-' }}</el-descriptions-item>
            <el-descriptions-item label="所属社区">{{ volunteerProfile.community_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="技能特长">{{ volunteerProfile.skills || '-' }}</el-descriptions-item>
            <el-descriptions-item label="累计服务工时">{{ volunteerProfile.total_service_hours ?? 0 }}</el-descriptions-item>
          </el-descriptions>
        </template>
      </div>
      <template #footer>
        <el-button @click="profileVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { asList } from '@/utils/request'
import { useUserStore } from '@/stores/user'
import type { Activity, Attendance, CommunityChangeRequest, Registration, User } from '@/types'
import { useIsMobile } from '@/composables/useIsMobile'

const userStore = useUserStore()
const { isMobile } = useIsMobile()
// 不同角色进入页面的默认签：系统管理员优先看账号审核，社区管理员看报名审核。
const activeTab = ref<'admin-account' | 'activity' | 'community-change' | 'registration' | 'attendance'>(
  userStore.isAdmin ? 'admin-account' : 'registration',
)

const users = ref<User[]>([])
const activities = ref<Activity[]>([])
const communityChanges = ref<CommunityChangeRequest[]>([])
const registrations = ref<Registration[]>([])
const attendances = ref<Attendance[]>([])
const volunteerProfile = ref<User | null>(null)
const profileVisible = ref(false)
const profileLoading = ref(false)
const adminAccountFilter = ref<'pending' | 'reviewed' | 'all'>('pending')
const activityFilter = ref<'pending' | 'reviewed' | 'all'>('pending')
const communityChangeFilter = ref<'pending' | 'reviewed' | 'all'>('pending')
const registrationFilter = ref<'pending' | 'reviewed' | 'all'>('pending')
const attendanceFilter = ref<'pending' | 'reviewed' | 'all'>('pending')

// 各标签的过滤结果（待审核/已审核/全部）。
const filteredCommunityAdmins = computed(() => {
  const list = users.value.filter(item => item.role === 'community_admin')
  if (adminAccountFilter.value === 'pending') {
    return list.filter(item => item.approval_status === 'pending')
  }
  if (adminAccountFilter.value === 'reviewed') {
    return list.filter(item => item.approval_status === 'approved' || item.approval_status === 'rejected')
  }
  return list
})

const filteredRegistrations = computed(() => {
  if (registrationFilter.value === 'pending') {
    return registrations.value.filter(item => item.status === 'pending')
  }
  if (registrationFilter.value === 'reviewed') {
    return registrations.value.filter(item => item.status === 'approved' || item.status === 'rejected')
  }
  return registrations.value
})

const filteredActivities = computed(() => {
  if (activityFilter.value === 'pending') {
    return activities.value.filter(item => item.review_status === 'pending')
  }
  if (activityFilter.value === 'reviewed') {
    return activities.value.filter(item => item.review_status === 'approved' || item.review_status === 'rejected')
  }
  return activities.value
})

const filteredCommunityChanges = computed(() => {
  if (communityChangeFilter.value === 'pending') {
    return communityChanges.value.filter(item => item.status === 'pending')
  }
  if (communityChangeFilter.value === 'reviewed') {
    return communityChanges.value.filter(item => item.status === 'approved' || item.status === 'rejected')
  }
  return communityChanges.value
})

const filteredAttendances = computed(() => {
  if (attendanceFilter.value === 'pending') {
    return attendances.value.filter(item => item.status === 'pending')
  }
  if (attendanceFilter.value === 'reviewed') {
    return attendances.value.filter(item => item.status === 'confirmed' || item.status === 'rejected')
  }
  return attendances.value
})

const fmt = (value?: string | null) => (value ? new Date(value).toLocaleString() : '-')

const adminApprovalText = (status?: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
  }
  return map[status || ''] || '-'
}

const adminApprovalType = (status?: string) => {
  const map: Record<string, 'warning' | 'success' | 'danger' | 'info'> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
  }
  return map[status || ''] || 'info'
}

const registrationStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    canceled: '已取消',
  }
  return map[status] || status
}

const activityStatusText = (status: string) => {
  const map: Record<string, string> = {
    unopened: '未开放',
    recruiting: '报名中',
    upcoming: '待开始',
    ongoing: '进行中',
    finished: '已结束',
  }
  return map[status] || status
}

const activityStatusType = (status: string) => {
  const map: Record<string, 'warning' | 'success' | 'danger' | 'info'> = {
    unopened: 'info',
    recruiting: 'success',
    upcoming: 'warning',
    ongoing: 'success',
    finished: 'info',
  }
  return map[status] || 'info'
}

const activityReviewStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
  }
  return map[status] || status
}

const activityReviewStatusType = (status: string) => {
  const map: Record<string, 'warning' | 'success' | 'danger' | 'info'> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
  }
  return map[status] || 'info'
}

const registrationStatusType = (status: string) => {
  const map: Record<string, 'warning' | 'success' | 'danger' | 'info'> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    canceled: 'info',
  }
  return map[status] || 'info'
}

const communityChangeStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
  }
  return map[status] || status
}

const communityChangeStatusType = (status: string) => {
  const map: Record<string, 'warning' | 'success' | 'danger' | 'info'> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
  }
  return map[status] || 'info'
}

const attendanceStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    confirmed: '已确认',
    rejected: '已驳回',
  }
  return map[status] || status
}

const attendanceStatusType = (status: string) => {
  const map: Record<string, 'warning' | 'success' | 'danger' | 'info'> = {
    pending: 'warning',
    confirmed: 'success',
    rejected: 'danger',
  }
  return map[status] || 'info'
}

// 以下 load* 方法对应各审核数据源。
const loadUsers = async () => {
  if (!userStore.isAdmin) return
  const { data } = await api.get('/users/')
  users.value = asList<User>(data)
}

const loadActivities = async () => {
  if (!userStore.isAdmin) return
  const { data } = await api.get('/activities/')
  activities.value = asList<Activity>(data)
}

const loadCommunityChanges = async () => {
  if (!userStore.isAdmin) return
  const { data } = await api.get('/community-change-requests/')
  communityChanges.value = asList<CommunityChangeRequest>(data)
}

const loadRegistrations = async () => {
  const { data } = await api.get('/registrations/')
  registrations.value = asList<Registration>(data)
}

const loadAttendances = async () => {
  const { data } = await api.get('/attendances/')
  attendances.value = asList<Attendance>(data)
}

// 进入页面后并行加载全部审核数据。
const loadAll = async () => {
  await Promise.all([loadUsers(), loadActivities(), loadCommunityChanges(), loadRegistrations(), loadAttendances()])
}

const handleAdminAccountCommand = async (row: User, command: string) => {
  if (command === 'approve') {
    await approveCommunityAdmin(row.id)
    return
  }
  if (command === 'reject') {
    await rejectCommunityAdmin(row.id)
  }
}

const approveCommunityAdmin = async (id: number) => {
  try {
    await api.post(`/users/${id}/approve/`, { approval_note: '系统管理员审核通过' })
    ElMessage.success('审核通过')
    await loadUsers()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const rejectCommunityAdmin = async (id: number) => {
  let note = ''
  try {
    const result = await ElMessageBox.prompt('请输入拒绝原因（可选）', '拒绝审核', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputPlaceholder: '拒绝原因',
    })
    note = result.value || ''
  } catch {
    return
  }

  try {
    await api.post(`/users/${id}/reject/`, { approval_note: note || '系统管理员审核拒绝' })
    ElMessage.success('已拒绝')
    await loadUsers()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

// 报名审核：统一通过 action 参数复用通过/拒绝流程。
const reviewRegistration = async (id: number, action: 'approve' | 'reject') => {
  let note = ''
  try {
    const result = await ElMessageBox.prompt('请输入审核备注（可选）', action === 'approve' ? '通过报名' : '拒绝报名', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputPlaceholder: '审核备注',
    })
    note = result.value || ''
  } catch {
    return
  }

  try {
    await api.post(`/registrations/${id}/${action}/`, { review_note: note })
    ElMessage.success('操作成功')
    await Promise.all([loadRegistrations(), loadAttendances()])
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const handleRegistrationCommand = async (row: Registration, command: string) => {
  if (command === 'approve') {
    await reviewRegistration(row.id, 'approve')
    return
  }
  if (command === 'reject') {
    await reviewRegistration(row.id, 'reject')
  }
}

const openVolunteerProfile = async (registration: Registration) => {
  profileVisible.value = true
  profileLoading.value = true
  volunteerProfile.value = null
  try {
    const { data } = await api.get(`/registrations/${registration.id}/volunteer-profile/`)
    volunteerProfile.value = data
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取志愿者资料失败')
    profileVisible.value = false
  } finally {
    profileLoading.value = false
  }
}

// 活动审核：系统管理员审批后决定是否进入生命周期流转。
const reviewActivity = async (id: number, decision: 'approved' | 'rejected') => {
  let note = ''
  try {
    const result = await ElMessageBox.prompt('请输入审核备注（可选）', decision === 'approved' ? '通过活动' : '拒绝活动', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputPlaceholder: '审核备注',
    })
    note = result.value || ''
  } catch {
    return
  }

  try {
    await api.post(`/activities/${id}/review/`, { decision, review_note: note })
    ElMessage.success('审核成功')
    await loadActivities()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const handleActivityCommand = async (row: Activity, command: string) => {
  if (command === 'approved' || command === 'rejected') {
    await reviewActivity(row.id, command)
  }
}

// 社区变更审核：通过后后端会同步更新志愿者所属社区。
const reviewCommunityChange = async (id: number, decision: 'approved' | 'rejected') => {
  let note = ''
  try {
    const result = await ElMessageBox.prompt(
      '请输入审核备注（可选）',
      decision === 'approved' ? '通过社区变更' : '拒绝社区变更',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        inputPlaceholder: '审核备注',
      },
    )
    note = result.value || ''
  } catch {
    return
  }

  try {
    await api.post(`/community-change-requests/${id}/review/`, { decision, review_note: note })
    ElMessage.success('审核成功')
    await Promise.all([loadCommunityChanges(), loadUsers()])
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const handleCommunityChangeCommand = async (row: CommunityChangeRequest, command: string) => {
  if (command === 'approved' || command === 'rejected') {
    await reviewCommunityChange(row.id, command)
  }
}

// 工时审核通过：支持管理员调整最终确认工时。
const confirmHours = async (id: number, defaultHours: number) => {
  let approvedHours = String(defaultHours)
  let note = ''
  try {
    const r1 = await ElMessageBox.prompt('请输入确认工时', '确认工时', {
      inputValue: String(defaultHours),
      inputPattern: /^\d+(\.\d{1,2})?$/,
      inputErrorMessage: '请输入合法工时',
      confirmButtonText: '下一步',
      cancelButtonText: '取消',
    })
    approvedHours = r1.value
    const r2 = await ElMessageBox.prompt('请输入审核备注（可选）', '审核备注', {
      confirmButtonText: '提交',
      cancelButtonText: '取消',
      inputPlaceholder: '审核备注',
    })
    note = r2.value || ''
  } catch {
    return
  }

  try {
    await api.post(`/attendances/${id}/confirm/`, {
      decision: 'confirmed',
      approved_hours: approvedHours,
      review_note: note,
    })
    ElMessage.success('工时已确认')
    await loadAttendances()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

// 工时审核驳回：将状态置为 rejected。
const rejectHours = async (id: number) => {
  let note = ''
  try {
    const result = await ElMessageBox.prompt('请输入驳回原因（可选）', '驳回工时', {
      confirmButtonText: '确认驳回',
      cancelButtonText: '取消',
      inputPlaceholder: '驳回原因',
    })
    note = result.value || ''
  } catch {
    return
  }

  try {
    await api.post(`/attendances/${id}/confirm/`, {
      decision: 'rejected',
      review_note: note,
    })
    ElMessage.success('已驳回')
    await loadAttendances()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const handleAttendanceCommand = async (row: Attendance, command: string) => {
  if (command === 'confirm') {
    await confirmHours(row.id, row.hours || 0)
    return
  }
  if (command === 'reject') {
    await rejectHours(row.id)
  }
}

onMounted(loadAll)
</script>


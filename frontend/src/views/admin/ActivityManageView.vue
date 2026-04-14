<template>
  <div class="view-page">
    <h2 class="page-title">活动管理</h2>
    <el-card>
      <template #header>
        <div class="card-header">
          <el-button type="primary" @click="openCreateDialog">发布活动</el-button>
          <el-button @click="loadActivities">刷新</el-button>
        </div>
      </template>

      <el-table :data="activities" border>
        <el-table-column prop="title" label="活动名称" min-width="180" />
        <el-table-column prop="community_name" label="社区" width="140" />
        <el-table-column label="类型" width="140">
          <template #default="{ row }">{{ row.type_display || row.type }}</template>
        </el-table-column>
        <el-table-column label="开始时间" width="180">
          <template #default="{ row }">{{ fmt(row.start_time) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审核" width="110">
          <template #default="{ row }">
            <el-tag :type="reviewStatusType(row.review_status)">{{ reviewStatusText(row.review_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" :min-width="isMobile ? 96 : 330" :fixed="isMobile ? undefined : 'right'">
          <template #default="{ row }">
            <template v-if="!isMobile">
              <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
              <el-button link type="danger" @click="removeActivity(row.id)">删除</el-button>
              <el-button
                v-if="row.review_status === 'approved' && ['recruiting', 'upcoming'].includes(row.status)"
                link
                type="success"
                @click="progressActivity(row.id, 'start')"
              >
                开始
              </el-button>
              <el-button
                v-if="row.review_status === 'approved' && row.status === 'ongoing'"
                link
                type="warning"
                @click="progressActivity(row.id, 'finish')"
              >
                结束
              </el-button>
            </template>
            <el-dropdown v-else trigger="click" @command="(command: string) => handleMobileCommand(row, command)">
              <el-button link type="primary">
                操作
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item command="delete">删除</el-dropdown-item>
                  <el-dropdown-item
                    v-if="row.review_status === 'approved' && ['recruiting', 'upcoming'].includes(row.status)"
                    command="start"
                  >
                    开始
                  </el-dropdown-item>
                  <el-dropdown-item v-if="row.review_status === 'approved' && row.status === 'ongoing'" command="finish">
                    结束
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑活动' : '发布活动'" width="740px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="活动名称" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="活动类型" required>
          <el-select v-model="form.activity_type" placeholder="请选择活动类型" style="width: 100%">
            <el-option v-for="item in activityTypes" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="useOtherType" label="类型补充" required>
          <el-input v-model="form.other_type" maxlength="80" show-word-limit placeholder="例如：防诈骗宣传" />
        </el-form-item>
        <el-form-item label="活动地点" required>
          <el-input v-model="form.location" />
        </el-form-item>
        <el-form-item v-if="userStore.isAdmin" label="发起社区" required>
          <el-select v-model="form.community" style="width: 100%">
            <el-option v-for="item in communities" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间" required>
          <el-date-picker v-model="form.start_time" type="datetime" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束时间" required>
          <el-date-picker v-model="form.end_time" type="datetime" style="width: 100%" />
        </el-form-item>
        <el-form-item label="报名截止" required>
          <el-date-picker v-model="form.deadline" type="datetime" style="width: 100%" />
        </el-form-item>
        <el-form-item label="招募人数" required>
          <el-input-number v-model="form.max_volunteers" :min="1" />
        </el-form-item>
        <el-form-item label="跨社区参与">
          <el-switch v-model="form.allow_external" />
        </el-form-item>
        <el-form-item label="活动描述" required>
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="封面图片">
          <el-upload :auto-upload="false" :show-file-list="false" accept="image/*" :on-change="handleCoverChange">
            <el-button>选择封面</el-button>
          </el-upload>
          <span class="meta-row" style="margin-left: 10px" v-if="form.cover_image">{{ form.cover_image.name }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { asList } from '@/utils/request'
import { useUserStore } from '@/stores/user'
import type { Activity, ActivityType, Community } from '@/types'
import { useIsMobile } from '@/composables/useIsMobile'

const userStore = useUserStore()
const { isMobile } = useIsMobile()
// 活动列表与下拉字典数据源。
const activities = ref<Activity[]>([])
const communities = ref<Community[]>([])
const activityTypes = ref<ActivityType[]>([])
// 新增/编辑弹窗状态。
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const form = ref({
  title: '',
  activity_type: undefined as number | undefined,
  other_type: '',
  location: '',
  community: undefined as number | undefined,
  start_time: null as Date | null,
  end_time: null as Date | null,
  deadline: null as Date | null,
  max_volunteers: 10,
  allow_external: false,
  description: '',
  cover_image: undefined as File | undefined,
})
const selectedTypeName = computed(() => {
  // 根据已选类型 ID 回推名称。
  const found = activityTypes.value.find(item => item.id === form.value.activity_type)
  return found?.name || ''
})
const useOtherType = computed(() => selectedTypeName.value === '其他')

const statusText = (status: string) => {
  const map: Record<string, string> = {
    unopened: '未开放',
    recruiting: '报名中',
    upcoming: '待开始',
    ongoing: '进行中',
    finished: '已结束',
  }
  return map[status] || status
}

const statusType = (status: string) => {
  const map: Record<string, any> = {
    unopened: 'info',
    recruiting: 'success',
    upcoming: 'warning',
    ongoing: 'success',
    finished: 'info',
  }
  return map[status] || 'info'
}

const reviewStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
  }
  return map[status] || status
}

const reviewStatusType = (status: string) => {
  const map: Record<string, any> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
  }
  return map[status] || 'info'
}

const fmt = (value?: string) => (value ? new Date(value).toLocaleString() : '-')

const handleCoverChange = (uploadFile: { raw?: File }) => {
  // 上传前仅做格式校验，避免错误文件提交。
  const file = uploadFile.raw
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请上传图片格式的封面文件')
    form.value.cover_image = undefined
    return
  }
  form.value.cover_image = file
}

const resetForm = () => {
  // 重置表单，保证“新增”活动使用干净状态。
  form.value = {
    title: '',
    activity_type: undefined,
    other_type: '',
    location: '',
    community: undefined,
    start_time: null,
    end_time: null,
    deadline: null,
    max_volunteers: 10,
    allow_external: false,
    description: '',
    cover_image: undefined,
  }
  editingId.value = null
}

const openCreateDialog = () => {
  resetForm()
  dialogVisible.value = true
}

const openEditDialog = (row: Activity) => {
  // 编辑时按活动详情回填表单。
  editingId.value = row.id
  form.value.title = row.title
  form.value.activity_type = row.activity_type || undefined
  form.value.other_type = row.other_type || ''
  form.value.location = row.location
  form.value.community = row.community
  form.value.start_time = row.start_time ? new Date(row.start_time) : null
  form.value.end_time = row.end_time ? new Date(row.end_time) : null
  form.value.deadline = row.deadline ? new Date(row.deadline) : null
  form.value.max_volunteers = row.max_volunteers
  form.value.allow_external = row.allow_external
  form.value.description = row.description
  form.value.cover_image = undefined
  dialogVisible.value = true
}

const buildFormData = () => {
  // 统一构建 multipart/form-data，兼容图片上传。
  const payload = new FormData()
  payload.append('title', form.value.title)
  payload.append('activity_type', String(form.value.activity_type || ''))
  if (useOtherType.value && form.value.other_type.trim()) {
    payload.append('other_type', form.value.other_type.trim())
  }
  payload.append('location', form.value.location)
  payload.append('start_time', form.value.start_time ? form.value.start_time.toISOString() : '')
  payload.append('end_time', form.value.end_time ? form.value.end_time.toISOString() : '')
  payload.append('deadline', form.value.deadline ? form.value.deadline.toISOString() : '')
  payload.append('max_volunteers', String(form.value.max_volunteers))
  payload.append('allow_external', String(form.value.allow_external))
  payload.append('description', form.value.description)
  if (userStore.isAdmin && form.value.community) {
    payload.append('community', String(form.value.community))
  }
  if (form.value.cover_image) {
    payload.append('cover_image', form.value.cover_image)
  }
  return payload
}

const submitForm = async () => {
  // 提交前做前端关键校验，减少后端无效请求。
  if (!form.value.activity_type) {
    ElMessage.warning('请选择活动类型')
    return
  }
  if (useOtherType.value && !form.value.other_type.trim()) {
    ElMessage.warning('选择“其他”时请填写类型补充')
    return
  }
  saving.value = true
  try {
    const payload = buildFormData()
    if (editingId.value) {
      await api.patch(`/activities/${editingId.value}/`, payload)
      ElMessage.success('活动已更新')
    } else {
      await api.post('/activities/', payload)
      ElMessage.success('活动已创建，等待系统管理员审核')
    }
    dialogVisible.value = false
    await loadActivities()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.response?.data?.non_field_errors?.[0] || '操作失败')
  } finally {
    saving.value = false
  }
}

const removeActivity = async (id: number) => {
  // 删除活动前二次确认。
  await ElMessageBox.confirm('确认删除该活动吗？', '提示', { type: 'warning' })
  try {
    await api.delete(`/activities/${id}/`)
    ElMessage.success('删除成功')
    await loadActivities()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

const progressActivity = async (id: number, action: 'start' | 'finish') => {
  // 管理员推进活动生命周期（开始/结束）。
  try {
    await api.post(`/activities/${id}/${action}/`)
    ElMessage.success(action === 'start' ? '活动已开始' : '活动已结束')
    await loadActivities()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const handleMobileCommand = async (row: Activity, command: string) => {
  // 移动端下拉命令分发。
  if (command === 'edit') {
    openEditDialog(row)
    return
  }
  if (command === 'delete') {
    await removeActivity(row.id)
    return
  }
  if (command === 'start') {
    await progressActivity(row.id, 'start')
    return
  }
  if (command === 'finish') {
    await progressActivity(row.id, 'finish')
  }
}

const loadActivities = async () => {
  // 加载当前角色可管理活动。
  const { data } = await api.get('/activities/')
  activities.value = asList<Activity>(data)
}

const loadCommunities = async () => {
  // 系统管理员创建活动时可指定发起社区。
  if (!userStore.isAdmin) return
  const { data } = await api.get('/communities/')
  communities.value = asList<Community>(data)
}

const loadActivityTypes = async () => {
  // 活动类型用于表单下拉和“其他”类型判定。
  const { data } = await api.get('/activity-types/')
  activityTypes.value = asList<ActivityType>(data)
}

onMounted(async () => {
  // 页面初始化并行加载数据源。
  await Promise.all([loadActivities(), loadCommunities(), loadActivityTypes()])
})
</script>


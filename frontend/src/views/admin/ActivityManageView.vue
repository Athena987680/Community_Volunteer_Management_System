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
        <el-table-column label="操作" min-width="330" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="removeActivity(row.id)">删除</el-button>
            <el-button v-if="row.status === 'approved'" link type="success" @click="progressActivity(row.id, 'start')">开始</el-button>
            <el-button v-if="row.status === 'ongoing'" link type="warning" @click="progressActivity(row.id, 'finish')">结束</el-button>
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

const userStore = useUserStore()
const activities = ref<Activity[]>([])
const communities = ref<Community[]>([])
const activityTypes = ref<ActivityType[]>([])
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
  const found = activityTypes.value.find(item => item.id === form.value.activity_type)
  return found?.name || ''
})
const useOtherType = computed(() => selectedTypeName.value === '其他')

const statusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    ongoing: '进行中',
    finished: '已结束',
  }
  return map[status] || status
}

const statusType = (status: string) => {
  const map: Record<string, any> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    ongoing: 'success',
    finished: 'info',
  }
  return map[status] || 'info'
}

const fmt = (value?: string) => (value ? new Date(value).toLocaleString() : '-')

const handleCoverChange = (uploadFile: { raw?: File }) => {
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
  try {
    await api.post(`/activities/${id}/${action}/`)
    ElMessage.success(action === 'start' ? '活动已开始' : '活动已结束')
    await loadActivities()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const loadActivities = async () => {
  const { data } = await api.get('/activities/')
  activities.value = asList<Activity>(data)
}

const loadCommunities = async () => {
  if (!userStore.isAdmin) return
  const { data } = await api.get('/communities/')
  communities.value = asList<Community>(data)
}

const loadActivityTypes = async () => {
  const { data } = await api.get('/activity-types/')
  activityTypes.value = asList<ActivityType>(data)
}

onMounted(async () => {
  await Promise.all([loadActivities(), loadCommunities(), loadActivityTypes()])
})
</script>


<template>
  <div class="view-page">
    <h2 class="page-title">用户管理</h2>
    <el-card>
      <template #header>
        <div class="card-header">
          <el-button type="primary" @click="openCreate">新增用户</el-button>
        </div>
      </template>
      <el-table :data="users" border>
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="real_name" label="姓名" width="120" />
        <el-table-column prop="role" label="角色" width="130">
          <template #default="{ row }">{{ roleText(row.role) }}</template>
        </el-table-column>
        <el-table-column label="社区" width="140">
          <template #default="{ row }">
            {{ row.role === 'system_admin' ? '-' : row.community_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column label="累计工时" width="100">
          <template #default="{ row }">
            {{ row.role === 'volunteer' ? (row.total_service_hours || 0) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="审核状态" width="130">
          <template #default="{ row }">
            <el-tag v-if="row.role === 'community_admin'" :type="approvalTagType(row.approval_status)">
              {{ approvalText(row.approval_status) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">{{ row.is_active ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="removeUser(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑用户' : '新增用户'" width="700px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" :disabled="!!editingId" />
        </el-form-item>
        <el-form-item label="密码" :required="!editingId">
          <el-input v-model="form.password" type="password" placeholder="编辑时留空表示不改密码" />
        </el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="form.real_name" />
        </el-form-item>
        <el-form-item label="性别" required>
          <el-radio-group v-model="form.gender">
            <el-radio value="male">男</el-radio>
            <el-radio value="female">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="手机号" required>
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="年龄">
          <el-input-number v-model="form.age" :min="1" :max="120" />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="志愿者" value="volunteer" />
            <el-option label="社区管理员" value="community_admin" />
            <el-option label="系统管理员" value="system_admin" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="showCommunityField" label="所属社区">
          <el-select v-model="form.community" clearable style="width: 100%">
            <el-option v-for="item in communities" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="showSkillsField" label="技能特长">
          <el-input v-model="form.skills" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item label="头像">
          <el-upload :auto-upload="false" :show-file-list="false" accept="image/*" :on-change="handleAvatarChange">
            <el-button>选择头像</el-button>
          </el-upload>
          <span class="meta-row" style="margin-left: 10px" v-if="form.avatar">{{ form.avatar.name }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { asList } from '@/utils/request'
import type { User, Community } from '@/types'

const users = ref<User[]>([])
const communities = ref<Community[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const form = ref({
  username: '',
  password: '',
  real_name: '',
  gender: 'male' as 'male' | 'female',
  phone: '',
  age: undefined as number | undefined,
  role: 'volunteer' as 'volunteer' | 'community_admin' | 'system_admin',
  community: undefined as number | undefined,
  skills: '',
  is_active: true,
  avatar: undefined as File | undefined,
})

const showCommunityField = computed(() => form.value.role !== 'system_admin')
const showSkillsField = computed(() => form.value.role === 'volunteer')

watch(
  () => form.value.role,
  role => {
    if (role === 'system_admin') {
      form.value.community = undefined
      form.value.skills = ''
      return
    }
    if (role === 'community_admin') {
      form.value.skills = ''
    }
  },
)

const roleText = (role: string) => {
  const map: Record<string, string> = {
    volunteer: '志愿者',
    community_admin: '社区管理员',
    system_admin: '系统管理员',
  }
  return map[role] || role
}

const approvalText = (status?: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
  }
  return map[status || ''] || '已通过'
}

const approvalTagType = (status?: string) => {
  const map: Record<string, 'warning' | 'success' | 'danger' | 'info'> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
  }
  return map[status || ''] || 'success'
}

const handleAvatarChange = (uploadFile: { raw?: File }) => {
  const file = uploadFile.raw
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请上传图片格式的头像文件')
    form.value.avatar = undefined
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('头像文件大小不能超过 2MB')
    form.value.avatar = undefined
    return
  }
  form.value.avatar = file
}

const resetForm = () => {
  form.value = {
    username: '',
    password: '',
    real_name: '',
    gender: 'male',
    phone: '',
    age: undefined,
    role: 'volunteer',
    community: undefined,
    skills: '',
    is_active: true,
    avatar: undefined,
  }
  editingId.value = null
}

const openCreate = () => {
  resetForm()
  dialogVisible.value = true
}

const openEdit = (row: User) => {
  editingId.value = row.id
  form.value.username = row.username
  form.value.password = ''
  form.value.real_name = row.real_name || ''
  form.value.gender = (row.gender || 'male') as 'male' | 'female'
  form.value.phone = row.phone || ''
  form.value.age = row.age || undefined
  form.value.role = row.role
  form.value.community = row.community || undefined
  form.value.skills = row.skills || ''
  form.value.is_active = row.is_active ?? true
  form.value.avatar = undefined
  dialogVisible.value = true
}

const buildPayload = () => {
  const payload = new FormData()
  payload.append('username', form.value.username)
  if (form.value.password) payload.append('password', form.value.password)
  payload.append('real_name', form.value.real_name)
  payload.append('gender', form.value.gender)
  payload.append('phone', form.value.phone)
  if (form.value.age !== undefined) payload.append('age', String(form.value.age))
  payload.append('role', form.value.role)
  if (showCommunityField.value && form.value.community) payload.append('community', String(form.value.community))
  if (showSkillsField.value) payload.append('skills', form.value.skills)
  payload.append('is_active', String(form.value.is_active))
  if (form.value.avatar) payload.append('avatar', form.value.avatar)
  return payload
}

const submit = async () => {
  saving.value = true
  try {
    const payload = buildPayload()
    if (editingId.value) {
      await api.patch(`/users/${editingId.value}/`, payload)
      ElMessage.success('用户已更新')
    } else {
      await api.post('/users/', payload)
      ElMessage.success('用户已创建')
    }
    dialogVisible.value = false
    await loadUsers()
  } catch (error: any) {
    const detail = error.response?.data
    ElMessage.error(detail?.avatar?.[0] || detail?.detail || detail?.phone?.[0] || detail?.username?.[0] || '操作失败')
  } finally {
    saving.value = false
  }
}

const removeUser = async (id: number) => {
  await ElMessageBox.confirm('确认删除该用户吗？', '提示', { type: 'warning' })
  try {
    await api.delete(`/users/${id}/`)
    ElMessage.success('删除成功')
    await loadUsers()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

const loadUsers = async () => {
  const { data } = await api.get('/users/')
  users.value = asList<User>(data)
}

const loadCommunities = async () => {
  const { data } = await api.get('/communities/')
  communities.value = asList<Community>(data)
}

onMounted(async () => {
  await Promise.all([loadUsers(), loadCommunities()])
})
</script>


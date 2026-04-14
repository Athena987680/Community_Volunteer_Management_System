<template>
  <div class="view-page profile-view">
    <h2 class="page-title">个人中心</h2>

    <el-row v-if="userStore.isVolunteer" :gutter="16" class="stats-grid">
      <el-col :xs="24" :md="12" :lg="6" v-for="item in volunteerCards" :key="item.label">
        <el-card class="volunteer-stat-card">
          <div class="stat-label">{{ item.label }}</div>
          <div class="stat-value">{{ item.value }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="profile-content">
      <el-col :xs="24" :md="8">
        <el-card class="profile-summary-card">
          <div class="profile-panel" v-if="userStore.user">
            <el-avatar :size="88" :src="userStore.user.avatar">{{ userStore.user.real_name?.slice(0, 1) }}</el-avatar>
            <h3 class="name">{{ userStore.user.real_name || userStore.user.username }}</h3>
            <el-tag class="role-tag" round>{{ roleText(userStore.user.role) }}</el-tag>

            <div class="profile-meta-grid">
              <div class="meta-item" v-if="showCommunity">
                <span class="meta-label">所属社区</span>
                <span class="meta-value">{{ userStore.user.community_name || '-' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">手机号</span>
                <span class="meta-value">{{ userStore.user.phone || '-' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">年龄</span>
                <span class="meta-value">{{ userStore.user.age || '-' }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="16">
        <el-card class="profile-edit-card">
          <template #header>
            <div class="card-header">
              <div>
                <div class="edit-title">编辑资料</div>
                <div class="meta-row">更新后将立即同步到你的账号信息</div>
              </div>
              <el-button type="primary" :loading="saving" @click="saveProfile">保存</el-button>
            </div>
          </template>

          <el-form :model="form" label-width="96px" class="profile-form">
            <el-form-item label="姓名">
              <el-input v-model="form.real_name" />
            </el-form-item>
            <el-form-item label="性别">
              <el-radio-group v-model="form.gender">
                <el-radio value="male">男</el-radio>
                <el-radio value="female">女</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="form.phone" />
            </el-form-item>
            <el-form-item label="年龄">
              <el-input-number v-model="form.age" :min="1" :max="120" />
            </el-form-item>
            <el-form-item v-if="showCommunity" label="所属社区">
              <el-select v-model="form.community" :disabled="!canEditCommunityInProfile" clearable style="width: 100%">
                <el-option v-for="item in communities" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
              <div v-if="userStore.isVolunteer" class="meta-row" style="margin-top: 6px">
                修改所属社区后，点击保存将提交社区变更审核申请。
              </div>
              <div v-else class="meta-row" style="margin-top: 6px">社区管理员所属社区不可自行修改。</div>
            </el-form-item>
            <el-form-item v-if="showSkills" label="技能特长">
              <el-input v-model="form.skills" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item label="头像上传">
              <el-upload :auto-upload="false" :show-file-list="false" accept="image/*" :on-change="handleAvatarChange">
                <el-button>选择头像</el-button>
              </el-upload>
              <span v-if="form.avatar" class="meta-row" style="margin-left: 10px">{{ form.avatar.name }}</span>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { asList } from '@/utils/request'
import { useUserStore } from '@/stores/user'
import type { Community, OverviewStats } from '@/types'

const userStore = useUserStore()
const saving = ref(false)
const communities = ref<Community[]>([])
const volunteerOverview = ref<OverviewStats | null>(null)

// 编辑表单：与用户资料字段一一对应。
const form = ref({
  real_name: '',
  gender: 'male' as 'male' | 'female',
  phone: '',
  age: undefined as number | undefined,
  community: undefined as number | undefined,
  skills: '',
  avatar: undefined as File | undefined,
})

const showCommunity = computed(() => {
  return userStore.user?.role !== 'system_admin'
})

const canEditCommunityInProfile = computed(() => {
  return userStore.user?.role === 'volunteer'
})

const showSkills = computed(() => {
  return userStore.user?.role === 'volunteer'
})

// 志愿者个人统计卡片。
const volunteerCards = computed(() => {
  const data = volunteerOverview.value
  return [
    { label: '已通过报名', value: data?.approved_registrations || 0 },
    { label: '待审核报名', value: data?.pending_registrations || 0 },
    { label: '累计服务工时', value: data?.confirmed_hours || 0 },
    { label: '完成活动数', value: data?.attended_activities || 0 },
  ]
})

const roleText = (role: string) => {
  const map: Record<string, string> = {
    volunteer: '志愿者',
    community_admin: '社区管理员',
    system_admin: '系统管理员',
  }
  return map[role] || role
}

// 上传前做图片类型与体积校验。
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

// 用当前登录用户信息初始化表单。
const initForm = () => {
  if (!userStore.user) return
  form.value.real_name = userStore.user.real_name || ''
  form.value.gender = (userStore.user.gender || 'male') as 'male' | 'female'
  form.value.phone = userStore.user.phone || ''
  form.value.age = userStore.user.age || undefined
  form.value.community = userStore.user.community || undefined
  form.value.skills = userStore.user.skills || ''
}

// 个人中心下拉框需要社区列表。
const loadCommunities = async () => {
  const { data } = await api.get('/communities/')
  communities.value = asList<Community>(data)
}

const loadVolunteerOverview = async () => {
  if (!userStore.isVolunteer) return
  const { data } = await api.get('/stats/overview/')
  volunteerOverview.value = data
}

// 保存资料：若志愿者变更社区，转为“提交变更申请”流程。
const saveProfile = async () => {
  const currentCommunity = userStore.user?.community || undefined
  const selectedCommunity = form.value.community || undefined
  const hasCommunityChange = userStore.isVolunteer && currentCommunity !== selectedCommunity
  if (hasCommunityChange && !selectedCommunity) {
    ElMessage.warning('所属社区不能为空')
    return
  }

  if (hasCommunityChange) {
    try {
      await ElMessageBox.confirm(
        '检测到你修改了所属社区。确认后将提交社区变更申请，需系统管理员审核通过后生效。',
        '确认提交社区变更申请',
        {
          confirmButtonText: '确认提交',
          cancelButtonText: '取消',
          type: 'warning',
        },
      )
    } catch {
      return
    }
  }

  saving.value = true
  try {
    await userStore.updateProfile({
      real_name: form.value.real_name,
      gender: form.value.gender,
      phone: form.value.phone,
      age: form.value.age,
      community: userStore.isVolunteer ? undefined : form.value.community,
      skills: showSkills.value ? form.value.skills : undefined,
      avatar: form.value.avatar,
    })
    if (hasCommunityChange && selectedCommunity) {
      await api.post('/community-change-requests/', { to_community: selectedCommunity })
      form.value.community = currentCommunity
      ElMessage.success('资料已更新，社区变更申请已提交，等待系统管理员审核')
    } else {
      ElMessage.success('资料已更新')
    }
    form.value.avatar = undefined
  } catch (error: any) {
    ElMessage.error(
      error.response?.data?.avatar?.[0] ||
        error.response?.data?.detail ||
        error.response?.data?.non_field_errors?.[0] ||
        error.response?.data?.phone?.[0] ||
        '更新失败',
    )
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  if (!userStore.user) {
    await userStore.fetchUserInfo()
  }
  initForm()
  await Promise.all([loadCommunities(), loadVolunteerOverview()])
})
</script>

<style scoped>
.profile-view {
  gap: 18px;
}

.profile-content {
  align-items: stretch;
}

.volunteer-stat-card {
  overflow: hidden;
  border: 1px solid #d7e6f7;
  background: #f7fbff;
}

.volunteer-stat-card .stat-label {
  color: #5d7289;
}

.volunteer-stat-card .stat-value {
  color: #1f4f57;
}

.profile-summary-card :deep(.el-card__body) {
  padding: 16px;
}

.profile-summary-card,
.profile-edit-card {
  height: 100%;
}

.profile-panel {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.profile-panel .name {
  margin: 6px 0 0;
  font-size: 20px;
}

.role-tag {
  margin-top: 4px;
}

.profile-meta-grid {
  width: 100%;
  margin-top: 6px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  border-radius: 8px;
  background: #f6f9fd;
  border: 1px solid #e4edf8;
}

.meta-label {
  color: #6f8095;
  font-size: 13px;
}

.meta-value {
  color: #2c425c;
  font-weight: 600;
}

.profile-edit-card :deep(.el-card__body) {
  padding: 14px 16px 16px;
}

.edit-title {
  font-size: 15px;
  font-weight: 700;
  color: #23415c;
}

.profile-form {
  max-width: 760px;
}

@media (max-width: 900px) {
  .profile-panel .name {
    font-size: 20px;
  }
}
</style>


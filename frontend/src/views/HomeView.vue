<template>
  <el-container class="layout-container">
    <el-aside width="230px" class="layout-aside">
      <div class="brand">社区志愿服务系统</div>
      <el-menu router :default-active="$route.path" class="menu">
        <el-menu-item v-if="!userStore.isVolunteer" index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/activities">
          <el-icon><Calendar /></el-icon>
          <span>活动列表</span>
        </el-menu-item>
        <el-menu-item v-if="userStore.isVolunteer" index="/my-registrations">
          <el-icon><Document /></el-icon>
          <span>我的报名</span>
        </el-menu-item>
        <el-menu-item index="/notices">
          <el-icon><Bell /></el-icon>
          <span>通知公告</span>
        </el-menu-item>

        <el-sub-menu
          v-if="userStore.isCommunityAdmin || userStore.isAdmin"
          index="/manage"
          popper-class="manage-submenu-popper"
        >
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>管理端</span>
          </template>
          <el-menu-item index="/manage/activities"><span class="manage-item-text">活动管理</span></el-menu-item>
          <el-menu-item index="/manage/reviews"><span class="manage-item-text">审核管理</span></el-menu-item>
          <el-menu-item index="/manage/notices"><span class="manage-item-text">公告管理</span></el-menu-item>
          <el-menu-item v-if="userStore.isAdmin" index="/manage/users"><span class="manage-item-text">用户管理</span></el-menu-item>
          <el-menu-item v-if="userStore.isAdmin" index="/manage/communities"><span class="manage-item-text">社区管理</span></el-menu-item>
          <el-menu-item v-if="userStore.isAdmin" index="/manage/activity-types">
            <span class="manage-item-text">活动类型管理</span>
          </el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <span>个人中心</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <div class="user-role">{{ roleText }}</div>
          <div class="user-name">{{ userStore.user?.real_name || userStore.user?.username }}</div>
        </div>
        <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
      </el-header>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>

  <el-dialog
    v-model="profileDialogVisible"
    title="完善个人资料"
    width="640px"
    :close-on-click-modal="false"
    :show-close="false"
  >
    <div class="meta-row" style="margin-bottom: 12px">首次登录请先完善个人资料后再使用系统。</div>
    <el-form :model="profileForm" label-width="90px">
      <el-form-item label="姓名" required>
        <el-input v-model="profileForm.real_name" />
      </el-form-item>
      <el-form-item label="性别" required>
        <el-radio-group v-model="profileForm.gender">
          <el-radio value="male">男</el-radio>
          <el-radio value="female">女</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="手机号" required>
        <el-input v-model="profileForm.phone" />
      </el-form-item>
      <el-form-item label="年龄" required>
        <el-input-number v-model="profileForm.age" :min="1" :max="120" />
      </el-form-item>
      <el-form-item v-if="requireCommunity" label="所属社区" required>
        <el-select v-model="profileForm.community" clearable style="width: 100%">
          <el-option v-for="item in communities" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="allowSkills" label="技能特长">
        <el-input v-model="profileForm.skills" type="textarea" :rows="3" />
      </el-form-item>
      <el-form-item label="头像">
        <el-upload :auto-upload="false" :show-file-list="false" accept="image/*" :on-change="handleAvatarChange">
          <el-button>选择头像</el-button>
        </el-upload>
        <span v-if="profileForm.avatar" class="meta-row" style="margin-left: 10px">{{ profileForm.avatar.name }}</span>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="profileDialogVisible = false">稍后完善</el-button>
      <el-button type="primary" :loading="savingProfile" @click="submitProfile">保存资料</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import api, { asList } from '@/utils/request'
import type { Community } from '@/types'

const router = useRouter()
const userStore = useUserStore()
const profileDialogVisible = ref(false)
const savingProfile = ref(false)
const communities = ref<Community[]>([])

const profileForm = ref({
  real_name: '',
  gender: 'male' as 'male' | 'female',
  phone: '',
  age: undefined as number | undefined,
  community: undefined as number | undefined,
  skills: '',
  avatar: undefined as File | undefined,
})

const roleText = computed(() => {
  const role = userStore.user?.role
  const map: Record<string, string> = {
    volunteer: '志愿者端',
    community_admin: '社区管理端',
    system_admin: '系统管理端',
  }
  return map[role || ''] || ''
})

const requireCommunity = computed(() => {
  return userStore.user?.role === 'volunteer' || userStore.user?.role === 'community_admin'
})

const allowSkills = computed(() => {
  return userStore.user?.role === 'volunteer'
})

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

const handleAvatarChange = (uploadFile: { raw?: File }) => {
  const file = uploadFile.raw
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请上传图片格式的头像文件')
    profileForm.value.avatar = undefined
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('头像文件大小不能超过 2MB')
    profileForm.value.avatar = undefined
    return
  }
  profileForm.value.avatar = file
}

const loadCommunities = async () => {
  const { data } = await api.get('/communities/')
  communities.value = asList<Community>(data)
}

const initProfileForm = () => {
  const user = userStore.user
  if (!user) return
  profileForm.value.real_name = user.real_name || ''
  profileForm.value.gender = (user.gender || 'male') as 'male' | 'female'
  profileForm.value.phone = user.phone || ''
  profileForm.value.age = user.age || undefined
  profileForm.value.community = user.community || undefined
  profileForm.value.skills = user.skills || ''
  profileForm.value.avatar = undefined
}

const submitProfile = async () => {
  if (!profileForm.value.real_name || !profileForm.value.gender || !profileForm.value.phone || !profileForm.value.age) {
    ElMessage.warning('请先填写完整必填信息')
    return
  }
  if (requireCommunity.value && !profileForm.value.community) {
    ElMessage.warning('请先填写完整必填信息')
    return
  }

  savingProfile.value = true
  try {
    await userStore.updateProfile({
      real_name: profileForm.value.real_name,
      gender: profileForm.value.gender,
      phone: profileForm.value.phone,
      age: profileForm.value.age,
      community: profileForm.value.community,
      skills: allowSkills.value ? profileForm.value.skills : undefined,
      avatar: profileForm.value.avatar,
    })
    profileDialogVisible.value = false
    ElMessage.success('资料已完善')
  } catch (error: any) {
    ElMessage.error(
      error.response?.data?.avatar?.[0] || error.response?.data?.detail || error.response?.data?.phone?.[0] || '保存失败',
    )
  } finally {
    savingProfile.value = false
  }
}

onMounted(async () => {
  await loadCommunities()
  initProfileForm()
  if (userStore.user && !userStore.user.profile_completed) {
    profileDialogVisible.value = true
  }
})
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
}

.layout-aside {
  background: #1f5c52;
  border-right: 1px solid rgba(255, 255, 255, 0.15);
}

.brand {
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  padding: 18px 16px;
  letter-spacing: 0.5px;
}

.menu {
  border-right: none;
  background: transparent;
  --el-menu-bg-color: transparent;
  --el-menu-text-color: rgba(255, 255, 255, 0.88);
  --el-menu-active-color: #fff;
  --el-menu-hover-bg-color: rgba(255, 255, 255, 0.12);
  --el-menu-item-height: 44px;
}

:deep(.menu > .el-menu-item),
:deep(.menu > .el-sub-menu > .el-sub-menu__title) {
  color: rgba(255, 255, 255, 0.88);
}

:deep(.menu > .el-menu-item:hover),
:deep(.menu > .el-sub-menu > .el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.12);
}

:deep(.menu > .el-menu-item.is-active),
:deep(.menu > .el-sub-menu.is-active > .el-sub-menu__title) {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
}

:deep(.menu > .el-sub-menu .el-sub-menu__title .el-icon) {
  color: inherit;
}

:deep(.menu .el-sub-menu .el-menu-item) {
  color: rgba(255, 255, 255, 0.84);
  background: rgba(255, 255, 255, 0.05);
}

:deep(.menu .el-sub-menu .el-menu-item *),
:deep(.menu > .el-menu-item *),
:deep(.menu > .el-sub-menu > .el-sub-menu__title *) {
  color: inherit !important;
}

:deep(.menu .manage-item-text) {
  color: inherit !important;
  opacity: 1 !important;
}

:deep(.menu .el-sub-menu .el-menu-item:hover) {
  color: #fff;
  background: rgba(255, 255, 255, 0.14);
}

:deep(.menu .el-sub-menu .el-menu-item.is-active) {
  color: #fff;
  background: rgba(255, 255, 255, 0.2);
}

.layout-header {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(4px);
  border-bottom: 1px solid #e7edf5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.user-role {
  font-weight: 700;
}

.user-name {
  color: #6a7a8c;
}

.layout-main {
  padding: 18px;
}

@media (max-width: 900px) {
  .layout-header {
    padding: 0 12px;
  }

  .user-name {
    display: none;
  }
}
</style>

<style>
.manage-submenu-popper {
  border: 1px solid #e3ebf5;
  border-radius: 8px;
  box-shadow: 0 8px 26px rgba(34, 53, 79, 0.12);
  --el-menu-bg-color: #ffffff;
  --el-menu-text-color: #2a4158;
  --el-menu-active-color: #1f5c52;
  --el-menu-hover-bg-color: #edf6f3;
}

.manage-submenu-popper .el-menu-item {
  color: #2a4158 !important;
}

.manage-submenu-popper .el-menu-item * {
  color: inherit !important;
}

.manage-submenu-popper .manage-item-text {
  color: inherit !important;
  opacity: 1 !important;
}

.manage-submenu-popper .el-menu-item:hover {
  background: #edf6f3;
}

.manage-submenu-popper .el-menu-item.is-active {
  color: #1f5c52 !important;
  background: #e1f2ee;
}
</style>

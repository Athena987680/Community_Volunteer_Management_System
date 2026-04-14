<template>
  <div class="auth-wrap">
    <el-card class="auth-card">
      <h2 class="auth-title">用户注册</h2>
      <p class="meta-row" style="margin-bottom: 14px">
        社区管理员账号需要系统管理员审核后方可登录。
      </p>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>

        <el-form-item label="确认密码" prop="password2">
          <el-input v-model="form.password2" type="password" show-password />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="form.role">
            <el-radio value="volunteer">志愿者</el-radio>
            <el-radio value="community_admin">社区管理员</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="所属社区" prop="community">
          <el-select v-model="form.community" placeholder="请选择社区" clearable style="width: 100%">
            <el-option v-for="item in communities" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleRegister">注册</el-button>
          <el-button @click="$router.push('/login')">返回登录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import api, { asList } from '@/utils/request'
import type { Community } from '@/types'

const router = useRouter()
const userStore = useUserStore()
// 注册流程的表单状态与社区下拉数据。
const loading = ref(false)
const formRef = ref()
const communities = ref<Community[]>([])

const form = ref({
  username: '',
  password: '',
  password2: '',
  role: 'volunteer' as 'volunteer' | 'community_admin',
  community: undefined as number | undefined,
})

const validateConfirmPassword = (_: any, value: string, callback: (error?: Error) => void) => {
  // 二次密码校验，防止误输入。
  if (value !== form.value.password) {
    callback(new Error('两次输入密码不一致'))
    return
  }
  callback()
}

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  password2: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  community: [{ required: true, message: '请选择所属社区', trigger: 'change' }],
}

const loadCommunities = async () => {
  // 注册时选择所属社区的数据源。
  const { data } = await api.get('/communities/')
  communities.value = asList<Community>(data)
}

const handleRegister = async () => {
  // 表单校验通过后提交注册。
  await formRef.value.validate()
  loading.value = true
  try {
    await userStore.register({
      username: form.value.username,
      password: form.value.password,
      role: form.value.role,
      community: form.value.community,
    })

    if (form.value.role === 'community_admin') {
      ElMessage.success('注册成功，等待系统管理员审核后可登录')
    } else {
      ElMessage.success('注册成功，请登录并完善个人资料')
    }
    router.push('/login')
  } catch (error: any) {
    const detail = error.response?.data
    ElMessage.error(detail?.detail || detail?.username?.[0] || '注册失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadCommunities)
</script>

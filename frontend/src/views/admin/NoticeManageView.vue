<template>
  <div class="view-page">
    <h2 class="page-title">公告管理</h2>
    <el-card>
      <template #header>
        <div class="card-header">
          <el-button type="primary" @click="openCreate">发布公告</el-button>
        </div>
      </template>

      <el-table :data="notices" border>
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="community_name" label="社区" width="140">
          <template #default="{ row }">{{ row.community_name || '全局公告' }}</template>
        </el-table-column>
        <el-table-column prop="created_by_name" label="发布人" width="120" />
        <el-table-column label="发布时间" width="180">
          <template #default="{ row }">{{ fmt(row.publish_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="removeNotice(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑公告' : '发布公告'" width="680px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item v-if="userStore.isAdmin" label="所属社区">
          <el-select v-model="form.community" clearable style="width: 100%" placeholder="空为全局公告">
            <el-option v-for="item in communities" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="form.content" type="textarea" :rows="6" />
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
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { asList } from '@/utils/request'
import { useUserStore } from '@/stores/user'
import type { Notice, Community } from '@/types'

const userStore = useUserStore()
const notices = ref<Notice[]>([])
const communities = ref<Community[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const form = ref({
  title: '',
  content: '',
  community: undefined as number | undefined,
})

const fmt = (value: string) => new Date(value).toLocaleString()

const loadNotices = async () => {
  const requestConfig = userStore.isCommunityAdmin ? { params: { manage_scope: 1 } } : {}
  const { data } = await api.get('/notices/', requestConfig)
  notices.value = asList<Notice>(data)
}

const loadCommunities = async () => {
  if (!userStore.isAdmin) return
  const { data } = await api.get('/communities/')
  communities.value = asList<Community>(data)
}

const openCreate = () => {
  editingId.value = null
  form.value = { title: '', content: '', community: undefined }
  dialogVisible.value = true
}

const openEdit = (row: Notice) => {
  editingId.value = row.id
  form.value = {
    title: row.title,
    content: row.content,
    community: row.community || undefined,
  }
  dialogVisible.value = true
}

const submit = async () => {
  saving.value = true
  try {
    if (editingId.value) {
      await api.patch(`/notices/${editingId.value}/`, form.value)
      ElMessage.success('公告已更新')
    } else {
      await api.post('/notices/', form.value)
      ElMessage.success('公告已发布')
    }
    dialogVisible.value = false
    await loadNotices()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

const removeNotice = async (id: number) => {
  await ElMessageBox.confirm('确认删除该公告吗？', '提示', { type: 'warning' })
  try {
    await api.delete(`/notices/${id}/`)
    ElMessage.success('删除成功')
    await loadNotices()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

onMounted(async () => {
  await Promise.all([loadNotices(), loadCommunities()])
})
</script>


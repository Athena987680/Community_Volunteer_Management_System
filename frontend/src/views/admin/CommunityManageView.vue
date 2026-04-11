<template>
  <div class="view-page">
    <h2 class="page-title">社区管理</h2>
    <el-card>
      <template #header>
        <div class="card-header">
          <el-button type="primary" @click="openCreate">新增社区</el-button>
        </div>
      </template>

      <el-table :data="communities" border>
        <el-table-column label="封面" width="90">
          <template #default="{ row }">
            <el-image v-if="row.cover_image" :src="row.cover_image" fit="cover" style="width: 58px; height: 40px" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="社区名称" width="180" />
        <el-table-column prop="description" label="描述" min-width="260" />
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ fmt(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="removeCommunity(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑社区' : '新增社区'" width="680px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="社区名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="社区描述">
          <el-input v-model="form.description" type="textarea" :rows="5" />
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
        <el-button type="primary" :loading="saving" @click="submit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { asList } from '@/utils/request'
import type { Community } from '@/types'

const communities = ref<Community[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const form = ref({
  name: '',
  description: '',
  cover_image: undefined as File | undefined,
})

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
  form.value = { name: '', description: '', cover_image: undefined }
  editingId.value = null
}

const openCreate = () => {
  resetForm()
  dialogVisible.value = true
}

const openEdit = (row: Community) => {
  editingId.value = row.id
  form.value.name = row.name
  form.value.description = row.description || ''
  form.value.cover_image = undefined
  dialogVisible.value = true
}

const buildPayload = () => {
  const payload = new FormData()
  payload.append('name', form.value.name)
  payload.append('description', form.value.description)
  if (form.value.cover_image) {
    payload.append('cover_image', form.value.cover_image)
  }
  return payload
}

const submit = async () => {
  saving.value = true
  try {
    const payload = buildPayload()
    if (editingId.value) {
      await api.patch(`/communities/${editingId.value}/`, payload)
      ElMessage.success('社区已更新')
    } else {
      await api.post('/communities/', payload)
      ElMessage.success('社区已创建')
    }
    dialogVisible.value = false
    await loadCommunities()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.response?.data?.name?.[0] || '操作失败')
  } finally {
    saving.value = false
  }
}

const removeCommunity = async (id: number) => {
  await ElMessageBox.confirm('确认删除该社区吗？删除后相关数据会受影响。', '提示', { type: 'warning' })
  try {
    await api.delete(`/communities/${id}/`)
    ElMessage.success('删除成功')
    await loadCommunities()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

const loadCommunities = async () => {
  const { data } = await api.get('/communities/')
  communities.value = asList<Community>(data)
}

onMounted(loadCommunities)
</script>


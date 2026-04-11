<template>
  <div class="view-page">
    <h2 class="page-title">活动类型管理</h2>
    <el-card>
      <template #header>
        <div class="card-header">
          <el-button type="primary" @click="openCreate">新增类型</el-button>
          <el-button @click="loadTypes">刷新</el-button>
        </div>
      </template>

      <el-table :data="types" border>
        <el-table-column prop="name" label="类型名称" min-width="180" />
        <el-table-column prop="sort_order" label="排序" width="110" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="220" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="removeType(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑活动类型' : '新增活动类型'" width="620px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="类型名称" required>
          <el-input v-model="form.name" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="1" :max="9999" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="3" maxlength="200" show-word-limit />
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
import type { ActivityType } from '@/types'

const types = ref<ActivityType[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const form = ref({
  name: '',
  sort_order: 100,
  is_active: true,
  description: '',
})

const loadTypes = async () => {
  const { data } = await api.get('/activity-types/')
  types.value = asList<ActivityType>(data)
}

const resetForm = () => {
  form.value = {
    name: '',
    sort_order: 100,
    is_active: true,
    description: '',
  }
}

const openCreate = () => {
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

const openEdit = (row: ActivityType) => {
  editingId.value = row.id
  form.value = {
    name: row.name,
    sort_order: row.sort_order,
    is_active: row.is_active,
    description: row.description || '',
  }
  dialogVisible.value = true
}

const submit = async () => {
  const name = form.value.name.trim()
  if (!name) {
    ElMessage.warning('请输入活动类型名称')
    return
  }

  saving.value = true
  try {
    const payload = {
      name,
      sort_order: form.value.sort_order,
      is_active: form.value.is_active,
      description: form.value.description.trim(),
    }
    if (editingId.value) {
      await api.patch(`/activity-types/${editingId.value}/`, payload)
      ElMessage.success('活动类型已更新')
    } else {
      await api.post('/activity-types/', payload)
      ElMessage.success('活动类型已创建')
    }
    dialogVisible.value = false
    await loadTypes()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.name?.[0] || error.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

const removeType = async (id: number) => {
  await ElMessageBox.confirm('确认删除该活动类型吗？删除后仅影响后续可选项。', '提示', { type: 'warning' })
  try {
    await api.delete(`/activity-types/${id}/`)
    ElMessage.success('删除成功')
    await loadTypes()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

onMounted(loadTypes)
</script>

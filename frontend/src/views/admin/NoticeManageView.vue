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
        <el-table-column label="操作" :width="isMobile ? 88 : 180" :fixed="isMobile ? undefined : 'right'">
          <template #default="{ row }">
            <template v-if="!isMobile">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link type="danger" @click="removeNotice(row.id)">删除</el-button>
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
                </el-dropdown-menu>
              </template>
            </el-dropdown>
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
import { useIsMobile } from '@/composables/useIsMobile'

const userStore = useUserStore()
const { isMobile } = useIsMobile()
// 公告列表与社区字典数据。
const notices = ref<Notice[]>([])
const communities = ref<Community[]>([])
// 新增/编辑公告弹窗状态。
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
  // 社区管理员仅拉取其管理范围公告；系统管理员拉全量。
  const requestConfig = userStore.isCommunityAdmin ? { params: { manage_scope: 1 } } : {}
  const { data } = await api.get('/notices/', requestConfig)
  notices.value = asList<Notice>(data)
}

const loadCommunities = async () => {
  // 系统管理员可选择公告所属社区；社区管理员不需要该数据。
  if (!userStore.isAdmin) return
  const { data } = await api.get('/communities/')
  communities.value = asList<Community>(data)
}

const openCreate = () => {
  // 打开“发布公告”弹窗并清空表单。
  editingId.value = null
  form.value = { title: '', content: '', community: undefined }
  dialogVisible.value = true
}

const openEdit = (row: Notice) => {
  // 编辑时回填公告内容。
  editingId.value = row.id
  form.value = {
    title: row.title,
    content: row.content,
    community: row.community || undefined,
  }
  dialogVisible.value = true
}

const submit = async () => {
  // 根据 editingId 区分发布与编辑。
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
  // 删除公告前确认。
  await ElMessageBox.confirm('确认删除该公告吗？', '提示', { type: 'warning' })
  try {
    await api.delete(`/notices/${id}/`)
    ElMessage.success('删除成功')
    await loadNotices()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

const handleMobileCommand = async (row: Notice, command: string) => {
  // 移动端操作菜单命令分发。
  if (command === 'edit') {
    openEdit(row)
    return
  }
  if (command === 'delete') {
    await removeNotice(row.id)
  }
}

onMounted(async () => {
  // 页面初始化并行加载公告与社区字典。
  await Promise.all([loadNotices(), loadCommunities()])
})
</script>


<template>
  <div class="view-page">
    <h2 class="page-title">操作日志</h2>
    <el-card>
      <template #header>
        <div class="card-header">
          <el-input v-model="filters.keyword" placeholder="关键字（操作人/目标/路径）" clearable style="max-width: 260px" />
          <el-select v-model="filters.module" placeholder="模块" clearable style="width: 180px">
            <el-option v-for="item in moduleOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select v-model="filters.action" placeholder="操作" clearable style="width: 160px">
            <el-option v-for="item in actionOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select v-model="filters.status" placeholder="结果" clearable style="width: 140px">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
          <el-button type="primary" :loading="loading" @click="loadLogs">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </template>

      <template v-if="isMobile">
        <div v-loading="loading" class="log-card-list">
          <el-card v-for="row in logs" :key="row.id" class="log-card">
            <div class="log-title-row">
              <span class="log-title">{{ row.module }} / {{ row.action }}</span>
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </div>
            <div class="meta-row">时间：{{ fmt(row.created_at) }}</div>
            <div class="meta-row">操作人：{{ row.operator_name || row.operator_display || '-' }}</div>
            <div class="meta-row">目标：{{ row.target_display || '-' }}</div>
            <div class="meta-row">请求：{{ row.method }} {{ row.path }}</div>
            <div class="meta-row">状态码：{{ row.status_code }}</div>
            <div class="meta-row">IP：{{ row.ip_address || '-' }}</div>
            <el-button v-if="row.detail" link type="primary" @click="openDetail(row.detail)">查看详情</el-button>
          </el-card>
          <div v-if="!logs.length && !loading" class="meta-row">暂无日志</div>
        </div>
      </template>

      <el-table v-else v-loading="loading" :data="logs" border>
        <el-table-column label="时间" width="180">
          <template #default="{ row }">{{ fmt(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作人" width="140">
          <template #default="{ row }">{{ row.operator_name || row.operator_display || '-' }}</template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="140" />
        <el-table-column prop="action" label="操作" width="120" />
        <el-table-column label="结果" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'success' ? 'success' : 'danger'">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="目标" min-width="180">
          <template #default="{ row }">{{ row.target_display || '-' }}</template>
        </el-table-column>
        <el-table-column label="请求" min-width="220">
          <template #default="{ row }">{{ row.method }} {{ row.path }}</template>
        </el-table-column>
        <el-table-column prop="status_code" label="状态码" width="90" />
        <el-table-column label="详情" width="90">
          <template #default="{ row }">
            <el-button v-if="row.detail" link type="primary" @click="openDetail(row.detail)">查看</el-button>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="detailVisible" title="日志详情" width="720px">
      <pre class="log-detail">{{ currentDetail }}</pre>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api, { asList } from '@/utils/request'
import { useIsMobile } from '@/composables/useIsMobile'
import type { OperationLog } from '@/types'

const { isMobile } = useIsMobile()
// 列表加载状态与日志数据。
const loading = ref(false)
const logs = ref<OperationLog[]>([])
// 详情弹窗状态。
const detailVisible = ref(false)
const currentDetail = ref('')

// 筛选器：关键字、模块、操作类型、结果状态。
const filters = ref({
  keyword: '',
  module: '',
  action: '',
  status: '',
})

const moduleOptions = computed(() => [
  '用户管理',
  '社区管理',
  '活动类型管理',
  '活动管理',
  '审核管理',
  '社区变更审核',
  '报名审核',
  '工时审核',
  '公告管理',
])

const actionOptions = computed(() => [
  '新增',
  '更新',
  '删除',
  '通过',
  '拒绝',
  '审核',
  '开始活动',
  '结束活动',
  '确认工时',
  '取消',
])

const fmt = (value: string) => (value ? new Date(value).toLocaleString() : '-')

const loadLogs = async () => {
  // 将非空筛选项拼装到查询参数后请求日志接口。
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (filters.value.keyword) params.keyword = filters.value.keyword
    if (filters.value.module) params.module = filters.value.module
    if (filters.value.action) params.action = filters.value.action
    if (filters.value.status) params.status = filters.value.status
    const { data } = await api.get('/operation-logs/', { params })
    logs.value = asList<OperationLog>(data)
  } finally {
    loading.value = false
  }
}

const resetFilters = async () => {
  // 重置筛选后立即重新查询。
  filters.value = {
    keyword: '',
    module: '',
    action: '',
    status: '',
  }
  await loadLogs()
}

const openDetail = (detail?: string | null) => {
  // 打开详情弹窗展示结构化日志内容。
  currentDetail.value = detail || ''
  detailVisible.value = true
}

onMounted(loadLogs)
</script>

<style scoped>
.log-card-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.log-card .el-card__body {
  padding: 12px;
}

.log-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.log-title {
  font-weight: 700;
  color: #243b56;
}

.log-detail {
  max-height: 420px;
  overflow: auto;
  background: #f5f8fc;
  border: 1px solid #e2eaf5;
  border-radius: 8px;
  padding: 10px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>

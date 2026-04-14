<template>
  <div class="view-page">
    <h2 class="page-title">活动列表</h2>
    <el-card>
      <template #header>
        <div class="card-header">
          <el-input v-model="searchKeyword" placeholder="按活动名称搜索" clearable style="max-width: 260px" />
          <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 180px">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
      </template>

      <template v-if="userStore.isVolunteer">
        <el-row v-if="filteredActivities.length" :gutter="16" class="activity-card-grid">
          <el-col v-for="row in filteredActivities" :key="row.id" :xs="24" :sm="12" :lg="8">
            <el-card class="activity-card" shadow="hover">
              <el-image
                v-if="row.cover_image"
                :src="row.cover_image"
                fit="cover"
                class="activity-card-cover"
              />
              <div v-else class="activity-card-cover empty-cover">暂无封面</div>

              <div class="activity-card-body">
                <div class="activity-card-title">{{ row.title }}</div>
                <div class="meta-row">类型：{{ row.type_display || row.type }}</div>
                <div class="meta-row">地点：{{ row.location }}</div>
                <div class="meta-row">开始：{{ formatTime(row.start_time) }}</div>

                <div class="card-bottom-row">
                  <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
                  <el-button link type="primary" @click="goDetail(row.id)">查看详情</el-button>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <div v-else class="meta-row">暂无符合条件的活动</div>
      </template>

      <el-table v-else :data="filteredActivities" border>
        <el-table-column label="封面" width="92">
          <template #default="{ row }">
            <el-image v-if="row.cover_image" :src="row.cover_image" fit="cover" style="width: 60px; height: 40px" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="活动名称" min-width="200" />
        <el-table-column label="类型" width="140">
          <template #default="{ row }">{{ row.type_display || row.type }}</template>
        </el-table-column>
        <el-table-column prop="community_name" label="社区" width="140" />
        <el-table-column prop="location" label="地点" min-width="180" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="报名截止" width="180">
          <template #default="{ row }">{{ formatTime(row.deadline) }}</template>
        </el-table-column>
        <el-table-column label="操作" :width="isMobile ? 88 : 110" :fixed="isMobile ? undefined : 'right'">
          <template #default="{ row }">
            <el-button link type="primary" @click="goDetail(row.id)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api, { asList } from '@/utils/request'
import { useUserStore } from '@/stores/user'
import type { Activity } from '@/types'
import { useIsMobile } from '@/composables/useIsMobile'

const router = useRouter()
const userStore = useUserStore()
const { isMobile } = useIsMobile()
// 活动原始列表与筛选条件。
const activities = ref<Activity[]>([])
const searchKeyword = ref('')
const statusFilter = ref('')

// 志愿者不展示“未开放”状态，管理员展示全生命周期状态。
const statusOptions = computed(() => {
  if (userStore.isVolunteer) {
    return [
      { label: '报名中', value: 'recruiting' },
      { label: '待开始', value: 'upcoming' },
      { label: '进行中', value: 'ongoing' },
      { label: '已结束', value: 'finished' },
    ]
  }
  return [
    { label: '未开放', value: 'unopened' },
    { label: '报名中', value: 'recruiting' },
    { label: '待开始', value: 'upcoming' },
    { label: '进行中', value: 'ongoing' },
    { label: '已结束', value: 'finished' },
  ]
})

const filteredActivities = computed(() => {
  // 前端本地组合筛选：关键字 + 状态。
  return activities.value.filter((item) => {
    const matchName = !searchKeyword.value || item.title.includes(searchKeyword.value)
    const matchStatus = !statusFilter.value || item.status === statusFilter.value
    return matchName && matchStatus
  })
})

const statusText = (status: string) => {
  // 状态文案统一映射，避免模板内硬编码。
  const map: Record<string, string> = {
    unopened: '未开放',
    recruiting: '报名中',
    upcoming: '待开始',
    ongoing: '进行中',
    finished: '已结束',
  }
  return map[status] || status
}

const statusType = (status: string) => {
  // 状态标签颜色统一映射。
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    unopened: 'info',
    recruiting: 'success',
    upcoming: 'warning',
    ongoing: 'success',
    finished: 'info',
  }
  return map[status] || 'info'
}

const formatTime = (value?: string) => {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

// 跳转到活动详情页。
const goDetail = (id: number) => router.push(`/activities/${id}`)

const loadActivities = async () => {
  // 拉取当前角色可见活动（后端按角色做数据范围控制）。
  const { data } = await api.get('/activities/')
  activities.value = asList<Activity>(data)
}

onMounted(loadActivities)
</script>

<style scoped>
.activity-card-grid .el-col {
  margin-bottom: 16px;
}

.activity-card {
  overflow: hidden;
}

.activity-card-cover {
  width: 100%;
  height: 150px;
  border-radius: 8px;
  border: 1px solid #e5edf7;
}

.empty-cover {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8ea0b4;
  background: #f6f9fd;
}

.activity-card-body {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.activity-card-title {
  font-size: 16px;
  font-weight: 700;
  color: #223a55;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-bottom-row {
  margin-top: 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
</style>

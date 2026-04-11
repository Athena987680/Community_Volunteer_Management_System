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
        <el-table-column label="操作" width="110" fixed="right">
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

const router = useRouter()
const userStore = useUserStore()
const activities = ref<Activity[]>([])
const searchKeyword = ref('')
const statusFilter = ref('')

const statusOptions = computed(() => {
  if (userStore.isVolunteer) {
    return [
      { label: '已通过', value: 'approved' },
      { label: '进行中', value: 'ongoing' },
      { label: '已结束', value: 'finished' },
    ]
  }
  return [
    { label: '待审核', value: 'pending' },
    { label: '已通过', value: 'approved' },
    { label: '进行中', value: 'ongoing' },
    { label: '已结束', value: 'finished' },
    { label: '已拒绝', value: 'rejected' },
  ]
})

const filteredActivities = computed(() => {
  return activities.value.filter((item) => {
    const matchName = !searchKeyword.value || item.title.includes(searchKeyword.value)
    const matchStatus = !statusFilter.value || item.status === statusFilter.value
    return matchName && matchStatus
  })
})

const statusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    ongoing: '进行中',
    finished: '已结束',
  }
  return map[status] || status
}

const statusType = (status: string) => {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    ongoing: 'success',
    finished: 'info',
  }
  return map[status] || 'info'
}

const formatTime = (value?: string) => {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

const goDetail = (id: number) => router.push(`/activities/${id}`)

const loadActivities = async () => {
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

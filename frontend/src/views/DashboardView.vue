<template>
  <div class="view-page">
    <h2 class="page-title">仪表盘</h2>

    <el-row :gutter="16" class="stats-grid">
      <el-col :xs="24" :md="12" :lg="6" v-for="card in cards" :key="card.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">{{ card.value }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="userStore.isCommunityAdmin || userStore.isAdmin">
      <template #header>
        <div class="card-header">
          <span>志愿者服务时长排行</span>
        </div>
      </template>
      <el-table :data="rankings" size="small" empty-text="暂无数据">
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="volunteer_name" label="志愿者" />
        <el-table-column prop="community_name" label="社区" />
        <el-table-column prop="total_hours" label="总工时" width="120" />
        <el-table-column prop="activity_count" label="活动次数" width="120" />
      </el-table>
    </el-card>

    <el-card v-if="userStore.isAdmin">
      <template #header>
        <div class="card-header">
          <span>社区服务时长分布</span>
        </div>
      </template>
      <el-table :data="communityDistribution" size="small" empty-text="暂无数据">
        <el-table-column prop="community_name" label="社区" />
        <el-table-column prop="total_hours" label="总工时" width="120" />
        <el-table-column prop="participant_count" label="参与人数" width="120" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api, { asList } from '@/utils/request'
import { useUserStore } from '@/stores/user'
import type { CommunityDistributionItem, OverviewStats, ServiceRankingItem } from '@/types'

const userStore = useUserStore()
const overview = ref<OverviewStats | null>(null)
const rankings = ref<ServiceRankingItem[]>([])
const communityDistribution = ref<CommunityDistributionItem[]>([])

const cards = computed(() => {
  const data = overview.value || { role: userStore.role || 'volunteer' }
  if (userStore.isVolunteer) {
    return [
      { label: '已通过报名', value: data.approved_registrations || 0 },
      { label: '待审核报名', value: data.pending_registrations || 0 },
      { label: '累计服务工时', value: data.confirmed_hours || 0 },
      { label: '完成活动数', value: data.attended_activities || 0 },
    ]
  }
  return [
    { label: '活动总数', value: data.total_activities || 0 },
    { label: '待审活动', value: data.pending_activity_reviews || 0 },
    { label: '待审报名', value: data.pending_registration_reviews || 0 },
    { label: '待审工时', value: data.pending_attendance_reviews || 0 },
  ]
})

const loadData = async () => {
  const { data } = await api.get('/stats/overview/')
  overview.value = data
  if (userStore.isCommunityAdmin || userStore.isAdmin) {
    const rankingResp = await api.get('/stats/service_ranking/')
    rankings.value = asList<ServiceRankingItem>(rankingResp.data)
  }
  if (userStore.isAdmin) {
    const distResp = await api.get('/stats/community_distribution/')
    communityDistribution.value = asList<CommunityDistributionItem>(distResp.data)
  }
}

onMounted(loadData)
</script>


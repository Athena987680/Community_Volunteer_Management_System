<template>
  <div class="view-page">
    <h2 class="page-title">我的报名</h2>
    <el-card>
      <el-table :data="registrations" border>
        <el-table-column prop="activity_title" label="活动名称" min-width="200" />
        <el-table-column prop="apply_time" label="报名时间" width="180">
          <template #default="{ row }">{{ fmt(row.apply_time) }}</template>
        </el-table-column>
        <el-table-column label="报名状态" width="120">
          <template #default="{ row }">
            <el-tag :type="regType(row.status)">{{ regText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="签到" width="170">
          <template #default="{ row }">
            {{ attendanceOf(row.id)?.check_in_time ? fmt(attendanceOf(row.id)?.check_in_time || '') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="签退" width="170">
          <template #default="{ row }">
            {{ attendanceOf(row.id)?.check_out_time ? fmt(attendanceOf(row.id)?.check_out_time || '') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="工时审核" width="150">
          <template #default="{ row }">
            <el-tag v-if="attendanceOf(row.id)" :type="attType(attendanceOf(row.id)!.status)">
              {{ attText(attendanceOf(row.id)!.status) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="确认工时" width="100">
          <template #default="{ row }">
            {{ attendanceOf(row.id)?.approved_hours ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goDetail(row.activity)">查看活动</el-button>
            <el-button
              v-if="row.status === 'pending'"
              link
              type="danger"
              @click="cancelRegistration(row.id)"
            >
              取消报名
            </el-button>
            <el-button
              v-if="canCheckIn(row.id, row.status)"
              link
              type="success"
              @click="doCheckIn(attendanceOf(row.id)!.id)"
            >
              签到
            </el-button>
            <el-button
              v-if="canCheckOut(row.id, row.status)"
              link
              type="warning"
              @click="doCheckOut(attendanceOf(row.id)!.id)"
            >
              签退
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api, { asList } from '@/utils/request'
import type { Registration, Attendance } from '@/types'

const router = useRouter()
const registrations = ref<Registration[]>([])
const attendances = ref<Attendance[]>([])

const fmt = (value: string) => (value ? new Date(value).toLocaleString() : '-')

const regText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    canceled: '已取消',
  }
  return map[status] || status
}

const regType = (status: string) => {
  const map: Record<string, any> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    canceled: 'info',
  }
  return map[status] || 'info'
}

const attText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    confirmed: '已确认',
    rejected: '已拒绝',
  }
  return map[status] || status
}

const attType = (status: string) => {
  const map: Record<string, any> = {
    pending: 'warning',
    confirmed: 'success',
    rejected: 'danger',
  }
  return map[status] || 'info'
}

const attendanceOf = (registrationId: number) => {
  return attendances.value.find((item) => item.registration === registrationId)
}

const canCheckIn = (registrationId: number, registrationStatus: string) => {
  const record = attendanceOf(registrationId)
  return !!record && registrationStatus === 'approved' && !record.check_in_time
}

const canCheckOut = (registrationId: number, registrationStatus: string) => {
  const record = attendanceOf(registrationId)
  return !!record && registrationStatus === 'approved' && !!record.check_in_time && !record.check_out_time
}

const goDetail = (id: number) => router.push(`/activities/${id}`)

const loadData = async () => {
  const [regResp, attResp] = await Promise.all([api.get('/registrations/'), api.get('/attendances/')])
  registrations.value = asList<Registration>(regResp.data)
  attendances.value = asList<Attendance>(attResp.data)
}

const cancelRegistration = async (id: number) => {
  try {
    await api.post(`/registrations/${id}/cancel/`)
    ElMessage.success('报名已取消')
    await loadData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '取消失败')
  }
}

const doCheckIn = async (attendanceId: number) => {
  try {
    await api.post(`/attendances/${attendanceId}/check_in/`)
    ElMessage.success('签到成功')
    await loadData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '签到失败')
  }
}

const doCheckOut = async (attendanceId: number) => {
  try {
    await api.post(`/attendances/${attendanceId}/check_out/`)
    ElMessage.success('签退成功，等待工时审核')
    await loadData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '签退失败')
  }
}

onMounted(loadData)
</script>


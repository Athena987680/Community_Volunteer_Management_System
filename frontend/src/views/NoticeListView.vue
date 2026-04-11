<template>
  <div class="view-page">
    <h2 class="page-title">通知公告</h2>
    <el-timeline>
      <el-timeline-item v-for="notice in notices" :key="notice.id" :timestamp="fmt(notice.publish_time)">
        <el-card>
          <h3>{{ notice.title }}</h3>
          <p>{{ notice.content }}</p>
          <div class="meta-row" style="margin-top: 10px">
            <span>发布人：{{ notice.created_by_name }}</span>
            <span style="margin-left: 16px">社区：{{ notice.community_name || '全局' }}</span>
          </div>
        </el-card>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api, { asList } from '@/utils/request'
import type { Notice } from '@/types'

const notices = ref<Notice[]>([])

const fmt = (value: string) => new Date(value).toLocaleString()

const loadNotices = async () => {
  const { data } = await api.get('/notices/')
  notices.value = asList<Notice>(data)
}

onMounted(loadNotices)
</script>


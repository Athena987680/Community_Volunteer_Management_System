<template>
  <div class="view-page">
    <h2 class="page-title">活动详情</h2>
    <el-card v-if="activity">
      <template #header>
        <div class="card-header">
          <span>{{ activity.title }}</span>
          <el-tag :type="statusType(activity.status)">{{ statusText(activity.status) }}</el-tag>
        </div>
      </template>

      <el-row :gutter="18" class="detail-main-row">
        <el-col :xs="24" :md="8" class="detail-cover-col">
          <div class="cover-pane">
            <el-image v-if="activity.cover_image" :src="activity.cover_image" fit="cover" class="cover-image" />
            <div v-else class="no-cover">无封面</div>
          </div>
        </el-col>
        <el-col :xs="24" :md="16" class="detail-info-col">
          <div class="info-pane">
            <el-descriptions :column="1" border class="detail-desc">
              <el-descriptions-item label="活动类型">{{ activity.type_display || activity.type }}</el-descriptions-item>
              <el-descriptions-item label="活动地点">{{ activity.location }}</el-descriptions-item>
              <el-descriptions-item label="开始时间">{{ fmt(activity.start_time) }}</el-descriptions-item>
              <el-descriptions-item label="结束时间">{{ fmt(activity.end_time) }}</el-descriptions-item>
              <el-descriptions-item label="报名截止">{{ fmt(activity.deadline) }}</el-descriptions-item>
              <el-descriptions-item label="招募人数">{{ activity.max_volunteers }}</el-descriptions-item>
              <el-descriptions-item label="已通过人数">{{ activity.approved_count || 0 }}</el-descriptions-item>
              <el-descriptions-item label="所属社区">{{ activity.community_name }}</el-descriptions-item>
              <el-descriptions-item label="发布人">{{ activity.created_by_name }}</el-descriptions-item>
              <el-descriptions-item label="跨社区参与">{{ activity.allow_external ? '允许' : '仅本社区' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-col>
      </el-row>

      <el-divider />
      <p>{{ activity.description }}</p>

      <el-divider />
      <div class="action-row">
        <template v-if="userStore.isVolunteer">
          <el-button
            v-if="!registration && activity.status === 'approved'"
            type="primary"
            :loading="submitting"
            @click="registerActivity"
          >
            报名活动
          </el-button>
          <el-tag v-else-if="registration" :type="regStatusType(registration.status)">
            报名状态：{{ regStatusText(registration.status) }}
          </el-tag>
          <span v-else class="meta-row">当前活动状态不可报名</span>
        </template>

        <template v-if="(userStore.isAdmin || userStore.isCommunityAdmin) && ['approved', 'ongoing'].includes(activity.status)">
          <el-button v-if="activity.status === 'approved'" type="success" plain @click="updateProgress('start')">开始活动</el-button>
          <el-button v-if="activity.status === 'ongoing'" type="warning" plain @click="updateProgress('finish')">结束活动</el-button>
        </template>
      </div>

      <div v-if="activity.review_note" class="review-note">
        审核备注：{{ activity.review_note }}
      </div>

      <el-divider />
      <div class="comment-section">
        <div class="comment-title">活动评论</div>
        <div class="comment-editor">
          <div v-if="replyParentId" class="reply-tip">
            正在回复 @{{ replyTargetName }}
            <el-button link type="primary" @click="cancelReply">取消回复</el-button>
          </div>
          <el-input
            v-model="commentText"
            type="textarea"
            :rows="3"
            maxlength="600"
            show-word-limit
            placeholder="请输入评论内容"
          />
          <div class="comment-submit">
            <el-button type="primary" :loading="commentSubmitting" @click="submitComment">发表评论</el-button>
          </div>
        </div>

        <div v-loading="commentsLoading" class="comment-list">
          <div v-if="!commentsWithDepth.length" class="meta-row">暂无评论，欢迎发表第一条评论。</div>
          <div
            v-for="item in commentsWithDepth"
            :key="item.id"
            class="comment-item"
            :style="{ marginLeft: `${item.depth * 18}px` }"
          >
            <div class="comment-head">
              <div class="comment-user">
                <el-avatar :size="34" :src="item.author_avatar">
                  {{ item.author_name?.slice(0, 1) || 'U' }}
                </el-avatar>
                <div>
                  <div class="comment-user-line">
                    <span class="comment-name">{{ item.author_name }}</span>
                    <el-tag size="small" effect="plain">{{ roleText(item.author_role) }}</el-tag>
                  </div>
                  <div class="meta-row">{{ fmt(item.created_at) }}</div>
                </div>
              </div>
              <div class="comment-ops">
                <el-button v-if="!item.is_deleted" link @click="startReply(item)">回复</el-button>
                <el-button v-if="item.can_delete" link type="danger" @click="deleteComment(item)">删除</el-button>
              </div>
            </div>
            <div v-if="item.parent_author_name" class="meta-row">回复 @{{ item.parent_author_name }}</div>
            <div class="comment-content" :class="{ deleted: item.is_deleted }">{{ item.content }}</div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { asList } from '@/utils/request'
import { useUserStore } from '@/stores/user'
import type { Activity, ActivityComment, Registration, UserRole } from '@/types'

const route = useRoute()
const userStore = useUserStore()

const activity = ref<Activity | null>(null)
const registration = ref<Registration | null>(null)
const submitting = ref(false)
const comments = ref<ActivityComment[]>([])
const commentsLoading = ref(false)
const commentText = ref('')
const commentSubmitting = ref(false)
const replyParentId = ref<number | null>(null)
const replyTargetName = ref('')

const commentsWithDepth = computed(() => {
  return [...comments.value]
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    .filter(item => !item.is_deleted)
    .map(item => ({
      ...item,
      depth: item.parent ? 1 : 0,
    }))
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
  const map: Record<string, any> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    ongoing: 'success',
    finished: 'info',
  }
  return map[status] || 'info'
}

const roleText = (role?: UserRole) => {
  const map: Record<UserRole, string> = {
    volunteer: '志愿者',
    community_admin: '社区管理员',
    system_admin: '系统管理员',
  }
  if (!role) return '用户'
  return map[role] || '用户'
}

const regStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    canceled: '已取消',
  }
  return map[status] || status
}

const regStatusType = (status: string) => {
  const map: Record<string, any> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    canceled: 'info',
  }
  return map[status] || 'info'
}

const fmt = (value?: string) => (value ? new Date(value).toLocaleString() : '-')

const loadDetail = async () => {
  const id = route.params.id
  const { data } = await api.get(`/activities/${id}/`)
  activity.value = data

  await loadComments()

  if (userStore.isVolunteer) {
    const regResp = await api.get('/registrations/', { params: { activity: id } })
    const myRegs = asList<Registration>(regResp.data)
    registration.value = myRegs[0] || null
  }
}

const loadComments = async () => {
  if (!activity.value) return
  commentsLoading.value = true
  try {
    const { data } = await api.get('/activity-comments/', { params: { activity: activity.value.id } })
    comments.value = asList<ActivityComment>(data)
  } finally {
    commentsLoading.value = false
  }
}

const registerActivity = async () => {
  if (!activity.value) return
  submitting.value = true
  try {
    await api.post('/registrations/', { activity: activity.value.id })
    ElMessage.success('报名成功，等待审核')
    await loadDetail()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.response?.data?.non_field_errors?.[0] || '报名失败')
  } finally {
    submitting.value = false
  }
}

const startReply = (item: ActivityComment) => {
  replyParentId.value = item.id
  replyTargetName.value = item.author_name
}

const cancelReply = () => {
  replyParentId.value = null
  replyTargetName.value = ''
}

const submitComment = async () => {
  if (!activity.value) return
  if (!commentText.value.trim()) {
    ElMessage.warning('评论内容不能为空')
    return
  }
  commentSubmitting.value = true
  try {
    await api.post('/activity-comments/', {
      activity: activity.value.id,
      parent: replyParentId.value,
      content: commentText.value,
    })
    commentText.value = ''
    cancelReply()
    await loadComments()
    ElMessage.success('评论已发布')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.response?.data?.non_field_errors?.[0] || '发布失败')
  } finally {
    commentSubmitting.value = false
  }
}

const deleteComment = async (item: ActivityComment) => {
  await ElMessageBox.confirm('确认删除该评论吗？', '提示', { type: 'warning' })
  try {
    await api.delete(`/activity-comments/${item.id}/`)
    ElMessage.success('评论已删除')
    await loadComments()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

const updateProgress = async (action: 'start' | 'finish') => {
  if (!activity.value) return
  try {
    await api.post(`/activities/${activity.value.id}/${action}/`)
    ElMessage.success(action === 'start' ? '活动已开始' : '活动已结束')
    await loadDetail()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

onMounted(loadDetail)
</script>

<style scoped>
.no-cover {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8b9aae;
  border: 1px dashed #ced9e8;
  border-radius: 8px;
  background: #f7fafc;
}

.detail-main-row {
  align-items: stretch;
}

.detail-cover-col,
.detail-info-col {
  display: flex;
}

.cover-pane {
  width: 100%;
  aspect-ratio: 1 / 1;
  overflow: hidden;
}

.cover-image {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 8px;
  border: 1px solid #dce6f2;
}

.info-pane {
  width: 100%;
}

.detail-desc {
  width: 100%;
}

.action-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.review-note {
  margin-top: 12px;
  color: #5e6f84;
}

.comment-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.comment-title {
  font-size: 16px;
  font-weight: 700;
  color: #22374d;
}

.comment-editor {
  border: 1px solid #e4ecf7;
  border-radius: 10px;
  padding: 12px;
  background: #f9fbfe;
}

.reply-tip {
  margin-bottom: 8px;
  color: #4e657e;
  font-size: 13px;
}

.comment-submit {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.comment-item {
  border: 1px solid #e5edf7;
  border-radius: 10px;
  padding: 10px 12px;
  background: #fff;
}

.comment-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.comment-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.comment-user-line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.comment-name {
  font-weight: 600;
  color: #223a55;
}

.comment-content {
  margin-top: 6px;
  line-height: 1.6;
  color: #2f4661;
  white-space: pre-wrap;
}

.comment-content.deleted {
  color: #8d9cae;
}
</style>


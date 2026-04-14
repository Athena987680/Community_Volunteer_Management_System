import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import type { UserRole } from '@/types'

// 路由分为三类：认证页、业务页、管理页（角色受限）。
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
    },
    {
      path: '/',
      component: () => import('@/views/HomeView.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/dashboard' },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'activities',
          name: 'activities',
          component: () => import('@/views/ActivityListView.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'activities/:id',
          name: 'activity-detail',
          component: () => import('@/views/ActivityDetailView.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'my-registrations',
          name: 'my-registrations',
          component: () => import('@/views/MyRegistrationsView.vue'),
          meta: { requiresAuth: true, roles: ['volunteer'] as UserRole[] },
        },
        {
          path: 'notices',
          name: 'notices',
          component: () => import('@/views/NoticeListView.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/views/ProfileView.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'manage/activities',
          name: 'manage-activities',
          component: () => import('@/views/admin/ActivityManageView.vue'),
          // 活动管理：系统管理员与社区管理员均可访问。
          meta: { requiresAuth: true, roles: ['community_admin', 'system_admin'] as UserRole[] },
        },
        {
          path: 'manage/reviews',
          name: 'manage-reviews',
          component: () => import('@/views/admin/ReviewManageView.vue'),
          // 审核管理：系统管理员与社区管理员共用页面，不同角色显示不同标签。
          meta: { requiresAuth: true, roles: ['community_admin', 'system_admin'] as UserRole[] },
        },
        {
          path: 'manage/registrations',
          redirect: '/manage/reviews',
        },
        {
          path: 'manage/attendance',
          redirect: '/manage/reviews',
        },
        {
          path: 'manage/notices',
          name: 'manage-notices',
          component: () => import('@/views/admin/NoticeManageView.vue'),
          meta: { requiresAuth: true, roles: ['community_admin', 'system_admin'] as UserRole[] },
        },
        {
          path: 'manage/stats',
          redirect: '/dashboard',
        },
        {
          path: 'manage/users',
          name: 'manage-users',
          component: () => import('@/views/admin/UserManageView.vue'),
          // 用户管理仅系统管理员可访问。
          meta: { requiresAuth: true, roles: ['system_admin'] as UserRole[] },
        },
        {
          path: 'manage/communities',
          name: 'manage-communities',
          component: () => import('@/views/admin/CommunityManageView.vue'),
          meta: { requiresAuth: true, roles: ['system_admin'] as UserRole[] },
        },
        {
          path: 'manage/activity-types',
          name: 'manage-activity-types',
          component: () => import('@/views/admin/ActivityTypeManageView.vue'),
          meta: { requiresAuth: true, roles: ['system_admin'] as UserRole[] },
        },
        {
          path: 'manage/operation-logs',
          name: 'manage-operation-logs',
          component: () => import('@/views/admin/OperationLogView.vue'),
          // 操作审计日志仅系统管理员可查看。
          meta: { requiresAuth: true, roles: ['system_admin'] as UserRole[] },
        },
      ],
    },
  ],
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  // 无权限时的回退路径：志愿者回个人中心，管理员回仪表盘。
  const fallbackPath = userStore.user?.role === 'volunteer' ? '/profile' : '/dashboard'

  if (to.meta.requiresAuth) {
    // 目标路由要求登录，但当前没有有效登录态。
    if (!userStore.isLoggedIn) {
      next('/login')
      return
    }
    // 页面刷新后内存态丢失时，补拉当前用户信息。
    if (!userStore.user) {
      try {
        await userStore.fetchUserInfo()
      } catch {
        userStore.logout()
        next('/login')
        return
      }
    }
  }

  const allowRoles = to.meta.roles as UserRole[] | undefined
  // 管理端路由的角色白名单校验。
  if (allowRoles && userStore.user && !allowRoles.includes(userStore.user.role)) {
    next(fallbackPath)
    return
  }

  // 志愿者统一从个人中心进入，不展示管理员仪表盘。
  if (to.path === '/dashboard' && userStore.user?.role === 'volunteer') {
    next('/profile')
    return
  }

  // 已登录用户不应再访问登录/注册页。
  if ((to.path === '/login' || to.path === '/register') && userStore.isLoggedIn) {
    next(fallbackPath)
    return
  }

  next()
})

export default router

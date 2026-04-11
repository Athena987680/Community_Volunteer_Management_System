import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import type { UserRole } from '@/types'

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
          meta: { requiresAuth: true, roles: ['community_admin', 'system_admin'] as UserRole[] },
        },
        {
          path: 'manage/reviews',
          name: 'manage-reviews',
          component: () => import('@/views/admin/ReviewManageView.vue'),
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
      ],
    },
  ],
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const fallbackPath = userStore.user?.role === 'volunteer' ? '/profile' : '/dashboard'

  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      next('/login')
      return
    }
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
  if (allowRoles && userStore.user && !allowRoles.includes(userStore.user.role)) {
    next(fallbackPath)
    return
  }

  if (to.path === '/dashboard' && userStore.user?.role === 'volunteer') {
    next('/profile')
    return
  }

  if ((to.path === '/login' || to.path === '/register') && userStore.isLoggedIn) {
    next(fallbackPath)
    return
  }

  next()
})

export default router

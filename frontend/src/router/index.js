/**
 * router/index.js — 路由配置 + 角色守卫
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/LoginView.vue'),
    },
    {
        path: '/match',
        name: 'Match',
        component: () => import('@/views/MatchView.vue'),
        meta: { requiresAuth: true },
    },
    {
        path: '/admin/users',
        name: 'Admin',
        component: () => import('@/views/AdminView.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
        path: '/super/data',
        name: 'SuperData',
        component: () => import('@/views/SuperView.vue'),
        meta: { requiresAuth: true, requiresSuper: true },
    },
    {
        path: '/',
        redirect: '/match',
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
    const auth = useAuthStore()

    // 如果有 token 但还没获取用户信息，先获取
    if (auth.isLoggedIn && !auth.user) {
        await auth.fetchMe()
    }

    // 未登录 → 跳转登录页
    if (to.meta.requiresAuth && !auth.isLoggedIn) {
        return next('/login')
    }

    // 已登录访问登录页 → 跳转筛查页
    if (to.path === '/login' && auth.isLoggedIn) {
        return next('/match')
    }

    // 角色不足 → 静默降级到筛查页
    if (to.meta.requiresAdmin && !auth.isAdmin) {
        return next('/match')
    }

    if (to.meta.requiresSuper && !auth.isSuperAdmin) {
        return next('/match')
    }

    next()
})

export default router

/**
 * stores/auth.js — 登录态、用户信息、角色权限
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getMe as getMeApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
    const token = ref(localStorage.getItem('token') || '')
    const user = ref(null)

    // 计算属性：角色判断（组件中不要直接判断 role 字符串）
    const isLoggedIn = computed(() => !!token.value)
    const isSuperAdmin = computed(() => user.value?.role === 'super_admin')
    const isAdmin = computed(() => ['super_admin', 'admin'].includes(user.value?.role))

    async function login(username, password) {
        const data = await loginApi({ username, password })
        token.value = data.token
        user.value = data.user
        localStorage.setItem('token', data.token)
    }

    async function fetchMe() {
        try {
            const data = await getMeApi()
            user.value = data
        } catch {
            logout()
        }
    }

    function logout() {
        token.value = ''
        user.value = null
        localStorage.removeItem('token')
    }

    return { token, user, isLoggedIn, isSuperAdmin, isAdmin, login, fetchMe, logout }
})

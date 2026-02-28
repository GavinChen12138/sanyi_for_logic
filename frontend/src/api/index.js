/**
 * api/index.js — Axios 实例配置，统一拦截器
 */
import axios from 'axios'
import router from '@/router'

const request = axios.create({
    baseURL: '/api',
    timeout: 10000
})

// 请求拦截：自动注入 JWT
request.interceptors.request.use(config => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// 响应拦截：统一处理错误码
request.interceptors.response.use(
    response => {
        const { code, msg, data } = response.data
        if (code === 0) return data
        if (code === 4010) {
            // Token 过期，清除登录态跳转登录页
            localStorage.removeItem('token')
            router.push('/login')
        }
        return Promise.reject(new Error(msg || '请求失败'))
    },
    error => Promise.reject(error)
)

export default request

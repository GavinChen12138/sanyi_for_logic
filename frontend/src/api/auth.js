/**
 * api/auth.js — 认证相关接口
 */
import request from './index'

export const login = (data) => request.post('/auth/login', data)
export const getMe = () => request.get('/auth/me')

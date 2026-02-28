/**
 * api/admin.js — 账号管理接口
 */
import request from './index'

export const getUsers = () => request.get('/admin/users')
export const createUser = (data) => request.post('/admin/users', data)
export const resetPassword = (id, data) => request.put(`/admin/users/${id}/reset-password`, data)
export const changeRole = (id, data) => request.put(`/admin/users/${id}/role`, data)
export const changeStatus = (id, data) => request.put(`/admin/users/${id}/status`, data)

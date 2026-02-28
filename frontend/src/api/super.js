/**
 * api/super.js — 高校数据管理接口
 */
import request from './index'

export const getVersions = () => request.get('/super/schools/versions')
export const uploadSchools = (formData) => request.post('/super/schools/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
})
export const rollbackVersion = (id) => request.post(`/super/schools/versions/${id}/rollback`)
export const downloadVersion = (id) => `/api/super/schools/versions/${id}/download`
export const getSchoolsList = () => request.get('/super/schools/list')
export const getGroupDetail = (schoolId, groupId) => request.get(`/super/schools/${schoolId}/groups/${groupId}`)
export const editGroup = (schoolId, groupId, data) => request.put(`/super/schools/${schoolId}/groups/${groupId}`, data)

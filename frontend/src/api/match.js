/**
 * api/match.js — 匹配相关接口
 */
import request from './index'

export const matchSchools = (data) => request.post('/match', data)

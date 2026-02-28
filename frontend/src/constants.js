/**
 * constants.js — 前端常量定义
 */

// 学考等级选项
export const GRADE_OPTIONS = ['A', 'B', 'C', 'D', 'E']

// 选考科目列表
export const SUBJECT_OPTIONS = ['物理', '化学', '生物', '历史', '地理', '政治', '技术']

// 学考所有科目（10门必须全部填写）
export const ALL_XUEKAO_SUBJECTS = ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治', '技术']

// 学校标签筛选选项
export const FILTER_TAGS = ['中外合办', '公办一梯队', '公办二梯队', '民办学校', '省重点一梯队', '省重点二梯队', '高职']

// 状态颜色映射
export const STATUS_COLOR_MAP = {
    '可报考': 'success',
    '待确认': 'warning',
    '不可报考': 'danger'
}

// 角色名称映射
export const ROLE_LABEL_MAP = {
    'super_admin': '超级管理员',
    'admin': '管理员',
    'planner': '规划师'
}

// 角色选项（admin 创建账号用）
export const ROLE_OPTIONS_FOR_ADMIN = [
    { label: '规划师', value: 'planner' }
]

// 角色选项（super_admin 创建账号用）
export const ROLE_OPTIONS_FOR_SUPER = [
    { label: '规划师', value: 'planner' },
    { label: '管理员', value: 'admin' },
    { label: '超级管理员', value: 'super_admin' }
]

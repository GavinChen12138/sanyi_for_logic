<script setup>
/**
 * App.vue — 根组件，左侧可收缩侧边栏导航 + 路由出口
 */
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

// 侧边栏折叠状态
const collapsed = ref(false)

// 当前路由路径
const activeRoute = computed(() => router.currentRoute.value.path)

// 角色显示
const roleLabel = computed(() => {
  const r = auth.user?.role
  if (r === 'super_admin') return '超级管理员'
  if (r === 'admin') return '管理员'
  return '规划师'
})

// 导航菜单项
const menuItems = computed(() => {
  const items = []
  if (auth.isLoggedIn) {
    items.push({ path: '/match', label: '成绩筛查', icon: 'icon-search' })
    if (auth.isAdmin) {
      items.push({ path: '/admin/users', label: '账号管理', icon: 'icon-user' })
    }
    if (auth.isSuperAdmin) {
      items.push({ path: '/super/data', label: '数据管理', icon: 'icon-bar-chart' })
    }
  }
  return items
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <a-layout class="app-layout">
    <!-- 左侧导航 -->
    <a-layout-sider
      v-if="auth.isLoggedIn"
      class="app-sidebar"
      :width="220"
      :collapsed-width="64"
      :collapsed="collapsed"
      collapsible
      hide-trigger
    >
      <!-- Logo -->
      <div class="sidebar-header">
        <div class="logo-mark">
          <icon-apps :size="18" />
        </div>
        <span v-if="!collapsed" class="app-logo">辑课规划师</span>
      </div>

      <!-- 菜单 -->
      <a-menu
        :selected-keys="[activeRoute]"
        :collapsed="collapsed"
        class="sidebar-menu"
        @menu-item-click="(key) => router.push(key)"
      >
        <a-menu-item v-for="item in menuItems" :key="item.path">
          <template #icon><component :is="item.icon" /></template>
          {{ item.label }}
        </a-menu-item>
      </a-menu>

      <!-- 底部：用户 + 折叠按钮 -->
      <div class="sidebar-bottom">
        <!-- 用户信息 -->
        <a-dropdown trigger="click" position="top">
          <div class="user-card">
            <a-avatar :size="32" class="user-avatar">
              <template #icon><icon-user /></template>
            </a-avatar>
            <div v-if="!collapsed" class="user-detail">
              <div class="user-name">{{ auth.user?.name }}</div>
              <div class="user-role">{{ roleLabel }}</div>
            </div>
          </div>
          <template #content>
            <a-doption @click="handleLogout">
              <template #icon><icon-export /></template>
              退出登录
            </a-doption>
          </template>
        </a-dropdown>

        <!-- 折叠切换 -->
        <div class="collapse-row" @click="collapsed = !collapsed">
          <icon-menu-fold v-if="!collapsed" class="collapse-icon" />
          <icon-menu-unfold v-else class="collapse-icon" />
          <span v-if="!collapsed" class="collapse-text">收起菜单</span>
        </div>
      </div>
    </a-layout-sider>

    <!-- 主内容 -->
    <a-layout>
      <a-layout-content class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<style scoped>
.app-layout {
  height: 100vh;
  overflow: hidden;
}

/* ── 侧边栏 ── */
.app-sidebar {
  background: linear-gradient(180deg, #ffffff 0%, #F7F8FA 100%) !important;
  border-right: 1px solid var(--border-color);
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.03);
}

/* 让 sider 内部容器纵向 flex 铺满 */
.app-sidebar :deep(.arco-layout-sider-children) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* ── Logo ── */
.sidebar-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  padding: 0 16px;
  overflow: hidden;
  white-space: nowrap;
}

.logo-mark {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #165DFF, #6AA1FF);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(22, 93, 255, 0.25);
}

.app-logo {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

/* ── 菜单 ── */
.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: none !important;
  padding: 8px 0;
}

/* 菜单项选中态 */
.sidebar-menu :deep(.arco-menu-item.arco-menu-selected) {
  background: var(--primary-light) !important;
  color: var(--primary-color) !important;
  font-weight: 600;
  position: relative;
}

.sidebar-menu :deep(.arco-menu-item.arco-menu-selected)::before {
  content: '';
  position: absolute;
  left: 0;
  top: 6px;
  bottom: 6px;
  width: 3px;
  background: var(--primary-color);
  border-radius: 0 2px 2px 0;
}

/* 菜单项悬浮 */
.sidebar-menu :deep(.arco-menu-item:not(.arco-menu-selected):hover) {
  background: var(--bg-secondary) !important;
}

/* ── 底部区域 ── */
.sidebar-bottom {
  flex-shrink: 0;
  border-top: 1px solid var(--border-color);
  padding: 8px;
}

/* ── 用户卡片 ── */
.user-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-normal);
  overflow: hidden;
}

.user-card:hover {
  background: var(--bg-secondary);
}

.user-avatar {
  flex-shrink: 0;
  background: linear-gradient(135deg, #165DFF, #6AA1FF) !important;
}

.user-detail {
  min-width: 0;
  overflow: hidden;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 11px;
  color: var(--text-tertiary);
}

/* ── 折叠按钮 ── */
.collapse-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  margin-top: 4px;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-tertiary);
  transition: background var(--transition-normal), color var(--transition-normal);
  overflow: hidden;
  white-space: nowrap;
}

.collapse-row:hover {
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.collapse-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.collapse-text {
  font-size: 13px;
}

/* ── 主内容区 ── */
.app-main {
  height: 100%;
  overflow-y: auto;
  background: var(--bg-color);
}

/* ── 过渡动画 ── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-normal);
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

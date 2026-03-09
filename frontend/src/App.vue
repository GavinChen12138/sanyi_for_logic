<script setup>
/**
 * App.vue — 根组件，顶部导航 + 路由出口
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

// 当前路由路径
const activeRoute = computed(() => router.currentRoute.value.path)

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
    <a-layout-sider :width="240" class="app-sidebar" v-if="auth.isLoggedIn">
      <div class="sidebar-header">
        <span class="app-logo">辑课规划师系统</span>
      </div>

      <a-menu
        :selected-keys="[activeRoute]"
        class="sidebar-menu"
        @menu-item-click="(key) => router.push(key)"
      >
        <a-menu-item
          v-for="item in menuItems"
          :key="item.path"
        >
          <template #icon><component :is="item.icon" /></template>
          {{ item.label }}
        </a-menu-item>
      </a-menu>

      <div class="sidebar-footer">
        <a-dropdown trigger="click" position="top">
          <div class="user-info">
            <a-avatar :size="32">
              <template #icon><icon-user /></template>
            </a-avatar>
            <div class="user-text">
              <span class="user-name">{{ auth.user?.name }}</span>
              <span class="user-role">{{ auth.user?.role === 'super_admin' ? '超级管理员' : auth.user?.role === 'admin' ? '管理员' : '规划师' }}</span>
            </div>
            <icon-up />
          </div>
          <template #content>
            <a-doption @click="handleLogout">
              <template #icon><icon-export /></template>
              退出登录
            </a-doption>
          </template>
        </a-dropdown>
      </div>
    </a-layout-sider>

    <!-- 右侧容器 -->
    <a-layout class="app-main-container">
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
  background: var(--bg-color);
  overflow: hidden;
}

.app-sidebar {
  background: #fff;
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.04);
  z-index: 100;
}

.sidebar-header {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;
}

.app-logo {
  font-size: 18px;
  font-weight: 700;
  color: var(--primary-color);
  white-space: nowrap;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  overflow-y: auto;
  padding: 12px 0;
}

.sidebar-menu :deep(.arco-menu-item) {
  height: 50px;
  line-height: 50px;
  margin: 4px 12px;
  border-radius: 8px;
}

.sidebar-menu :deep(.arco-menu-selected) {
  background-color: var(--color-primary-light-1);
  font-weight: 600;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.user-info:hover {
  background-color: var(--color-fill-2);
}

.user-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 12px;
  color: var(--text-secondary);
}

.app-main-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.app-main {
  padding: 0; /* 留给内部路由页面自行设置 padding，通常内容带有顶层 margin 或内容区需要贴边 */
  height: 100%;
  overflow-y: auto;
  background-color: var(--bg-color);
}
</style>

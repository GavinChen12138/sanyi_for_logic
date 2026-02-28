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
    items.push({ path: '/match', label: '成绩筛查', icon: 'Search' })
    if (auth.isAdmin) {
      items.push({ path: '/admin/users', label: '账号管理', icon: 'User' })
    }
    if (auth.isSuperAdmin) {
      items.push({ path: '/super/data', label: '数据管理', icon: 'DataAnalysis' })
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
  <el-container class="app-layout">
    <!-- 顶部导航栏 -->
    <el-header v-if="auth.isLoggedIn" class="app-header">
      <div class="header-content">
        <div class="header-left">
          <span class="app-logo">📋 三位一体筛查</span>
          <el-menu
            :default-active="activeRoute"
            mode="horizontal"
            :ellipsis="false"
            router
            class="nav-menu"
          >
            <el-menu-item
              v-for="item in menuItems"
              :key="item.path"
              :index="item.path"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.label }}</span>
            </el-menu-item>
          </el-menu>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click">
            <span class="user-info">
              <el-avatar :size="32" icon="UserFilled" />
              <span class="user-name">{{ auth.user?.name }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  角色：{{ auth.user?.role === 'super_admin' ? '超级管理员' : auth.user?.role === 'admin' ? '管理员' : '规划师' }}
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-header>

    <!-- 主内容区 -->
    <el-main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-main>
  </el-container>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  background: var(--bg-color);
}

.app-header {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  padding: 0;
  height: 60px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.app-logo {
  font-size: 18px;
  font-weight: 700;
  color: var(--primary-color);
  white-space: nowrap;
}

.nav-menu {
  border-bottom: none !important;
}

.nav-menu .el-menu-item {
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--text-primary);
}

.user-name {
  font-size: 14px;
}

.app-main {
  padding: 0;
  min-height: calc(100vh - 60px);
}
</style>

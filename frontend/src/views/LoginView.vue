<script setup>
/**
 * LoginView.vue — 登录页面（毛玻璃风格）
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    Message.success('登录成功')
    router.push('/match')
  } catch (err) {
    Message.error(err.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <!-- 背景装饰圆 -->
    <div class="bg-circle bg-circle--1"></div>
    <div class="bg-circle bg-circle--2"></div>
    <div class="bg-circle bg-circle--3"></div>

    <div class="login-container">
      <div class="login-card">
        <!-- 顶部装饰条 -->
        <div class="card-accent"></div>

        <div class="login-header">
          <div class="login-logo">
            <icon-apps :size="28" />
          </div>
          <h1 class="login-title">辑课规划师系统</h1>
          <p class="login-subtitle">浙江辑课规划师规划系统</p>
        </div>

        <a-form
          ref="formRef"
          :model="form"
          :rules="rules"
          auto-label-width
          size="large"
          @keyup.enter="handleLogin"
        >
          <a-form-item field="username" hide-label>
            <a-input
              v-model="form.username"
              placeholder="用户名"
              allow-clear
            >
              <template #prefix>
                <icon-user />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item field="password" hide-label>
            <a-input-password
              v-model="form.password"
              placeholder="密码"
              allow-clear
            >
              <template #prefix>
                <icon-lock />
              </template>
            </a-input-password>
          </a-form-item>
          <a-form-item hide-label>
            <a-button
              type="primary"
              class="login-btn"
              :loading="loading"
              @click="handleLogin"
              long
            >
              登 录
            </a-button>
          </a-form-item>
        </a-form>

        <div class="login-footer">
          <span>辑课规划师系统 · 升学无忧</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #165DFF 0%, #306FFF 40%, #6AA1FF 100%);
  position: relative;
  overflow: hidden;
}

/* 背景装饰浮动圆 */
.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.12;
  background: #fff;
  pointer-events: none;
}

.bg-circle--1 {
  width: 600px;
  height: 600px;
  top: -200px;
  right: -100px;
  animation: float-slow 20s ease-in-out infinite alternate;
}

.bg-circle--2 {
  width: 400px;
  height: 400px;
  bottom: -120px;
  left: -80px;
  opacity: 0.08;
  animation: float-slow 15s ease-in-out infinite alternate-reverse;
}

.bg-circle--3 {
  width: 200px;
  height: 200px;
  top: 50%;
  left: 15%;
  opacity: 0.06;
  animation: float-slow 12s ease-in-out infinite alternate;
}

@keyframes float-slow {
  0% { transform: translate(0, 0) scale(1); }
  100% { transform: translate(30px, -20px) scale(1.05); }
}

.login-container {
  width: 100%;
  max-width: 420px;
  padding: 24px;
  position: relative;
  z-index: 1;
}

.login-card {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: var(--radius-xl);
  padding: 44px 36px 32px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15),
              0 0 0 1px rgba(255, 255, 255, 0.3);
  position: relative;
  overflow: hidden;
}

/* 顶部渐变装饰条 */
.card-accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #165DFF, #6AA1FF, #165DFF);
  background-size: 200% 100%;
  animation: accent-shimmer 3s linear infinite;
}

@keyframes accent-shimmer {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-logo {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #165DFF, #6AA1FF);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 16px rgba(22, 93, 255, 0.3);
}

.login-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  letter-spacing: -0.02em;
}

.login-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  border-radius: var(--radius-md);
  transition: box-shadow var(--transition-normal);
}

.login-btn:hover {
  box-shadow: 0 4px 16px rgba(22, 93, 255, 0.35);
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 减少动效 */
@media (prefers-reduced-motion: reduce) {
  .bg-circle { animation: none; }
  .card-accent { animation: none; }
}
</style>

/**
 * main.js — Vue 应用入口
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ArcoVue from '@arco-design/web-vue'
import '@arco-design/web-vue/dist/arco.css'
import ArcoVueIcon from '@arco-design/web-vue/es/icon'

import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

// 注册 Arco Design 及图标
app.use(ArcoVue)
app.use(ArcoVueIcon)

// 注册 Pinia 和 Router
app.use(createPinia())
app.use(router)

app.mount('#app')

import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

// 创建根应用实例。
const app = createApp(App)

// 批量注册 Element Plus 图标组件，模板里可直接使用。
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 按顺序挂载状态、路由和 UI 组件库。
app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 挂载到页面根节点。
app.mount('#app')

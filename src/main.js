import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index.js'
import 'bootstrap/dist/css/bootstrap.min.css'

// 创建Vue应用实例
const app = createApp(App)

// 使用路由
app.use(router)

// 全局配置
app.config.globalProperties.$apiBaseUrl = '/api'

// 挂载应用
app.mount('#app')

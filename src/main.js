import { createApp } from 'vue'
import App from './App.vue'
import 'bootstrap/dist/css/bootstrap.min.css'

// 创建Vue应用实例
const app = createApp(App)

// 全局配置
app.config.globalProperties.$apiBaseUrl = '/api'

// 挂载应用
app.mount('#app')

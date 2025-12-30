<template>
  <div class="container-fluid py-4">
    <div class="row justify-content-center">
      <div class="col-12 col-lg-10 col-xl-8">
        <!-- 应用标题 -->
        <div class="text-center mb-4">
          <h1 class="display-4 fw-bold text-white mb-2">
            <i class="fas fa-music me-2"></i>
            音乐下载器
          </h1>
          <p class="lead text-white-50">支持搜索、批量下载音乐</p>
        </div>

        <!-- 主内容区域 -->
        <div class="app-container p-4">
          <!-- 导航标签 -->
          <ul class="nav nav-tabs nav-justified mb-4" id="functionTabs" role="tablist">
            <li class="nav-item" v-for="tab in tabs" :key="tab.id">
              <router-link 
                :to="tab.path"
                class="nav-link"
                active-class="active"
                exact-active-class="active"
              >
                <i :class="tab.icon" class="me-2"></i>
                {{ tab.name }}
              </router-link>
            </li>
          </ul>

          <!-- 功能区域 -->
          <div class="tab-content">
            <router-view></router-view>
          </div>
        </div>

        <!-- 全局消息提示 -->
        <div v-if="globalMessage.show" 
             class="alert" 
             :class="globalMessage.type === 'success' ? 'alert-success' : 'alert-danger'"
             role="alert">
          {{ globalMessage.text }}
        </div>
      </div>
    </div>
    
    <!-- 二维码登录组件 -->
    <QRLoginComponent />
  </div>
</template>

<script>
import { reactive } from 'vue'
import QRLoginComponent from './components/QRLoginComponent.vue'

export default {
  name: 'App',
  components: {
    QRLoginComponent
  },
  setup() {
    const globalMessage = reactive({
      show: false,
      text: '',
      type: 'success'
    })

    const tabs = [
      { id: 'search', name: '音乐搜索', icon: 'fas fa-search', path: '/search' },
      { id: 'playlist-download', name: '歌单搜索', icon: 'fas fa-layer-group', path: '/playlist-download' },
      { id: 'artist-download', name: '歌手搜索', icon: 'fas fa-user', path: '/artist-download' },
      { id: 'hot-playlists', name: '热门歌单', icon: 'fas fa-fire', path: '/hot-playlists' },
      { id: 'task-manager', name: '任务管理', icon: 'fas fa-tasks', path: '/task-manager' }
    ]

    // 显示全局消息
    const showMessage = (text, type = 'success', duration = 3000) => {
      globalMessage.text = text
      globalMessage.type = type
      globalMessage.show = true
      
      setTimeout(() => {
        globalMessage.show = false
      }, duration)
    }

    // 将showMessage函数挂载到window对象，供apiService调用
    if (typeof window !== 'undefined') {
      window.showGlobalMessage = showMessage
    }

    return {
      tabs,
      globalMessage,
      showMessage
    }
  }
}
</script>

<style scoped>
.tab-content {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.nav-link {
  cursor: pointer;
  text-decoration: none;
  color: inherit;
}

.nav-link:hover {
  text-decoration: none;
}
</style>

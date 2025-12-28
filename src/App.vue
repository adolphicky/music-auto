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
              <button 
                class="nav-link" 
                :class="{ active: activeTab === tab.id }"
                @click="activeTab = tab.id"
                type="button"
              >
                <i :class="tab.icon" class="me-2"></i>
                {{ tab.name }}
              </button>
            </li>
          </ul>

          <!-- 功能区域 -->
          <div class="tab-content">
            <!-- 搜索功能 -->
            <div v-if="activeTab === 'search'" class="tab-pane fade show active">
              <SearchComponent />
            </div>

            <!-- 歌单批量下载 -->
            <div v-if="activeTab === 'playlist-download'" class="tab-pane fade show active">
              <PlaylistSearchComponent />
            </div>

            <!-- 歌手批量下载 -->
            <div v-if="activeTab === 'artist-download'" class="tab-pane fade show active">
              <ArtistDownloadComponent />
            </div>

            <!-- 热门歌单 -->
            <div v-if="activeTab === 'hot-playlists'" class="tab-pane fade show active">
              <HotPlaylistsComponent />
            </div>
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
import { ref, reactive } from 'vue'
import SearchComponent from './components/SearchComponent.vue'
import PlaylistSearchComponent from './components/PlaylistSearchComponent.vue'
import ArtistDownloadComponent from './components/ArtistDownloadComponent.vue'
import HotPlaylistsComponent from './components/HotPlaylistsComponent.vue'
import QRLoginComponent from './components/QRLoginComponent.vue'

export default {
  name: 'App',
  components: {
    SearchComponent,
    PlaylistSearchComponent,
    ArtistDownloadComponent,
    HotPlaylistsComponent,
    QRLoginComponent
  },
  setup() {
    const activeTab = ref('search')
    const globalMessage = reactive({
      show: false,
      text: '',
      type: 'success'
    })

    const tabs = [
      { id: 'search', name: '音乐搜索', icon: 'fas fa-search' },
      { id: 'playlist-download', name: '歌单搜索', icon: 'fas fa-layer-group' },
      { id: 'artist-download', name: '歌手搜索', icon: 'fas fa-user' },
      { id: 'hot-playlists', name: '热门歌单', icon: 'fas fa-fire' }
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
      activeTab,
      tabs,
      globalMessage,
      showMessage
    }
  }
}
</script>

<style scoped>
.tab-pane {
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
</style>

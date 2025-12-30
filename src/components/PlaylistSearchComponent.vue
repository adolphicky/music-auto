<template>
  <div>
    <!-- 搜索框 -->
    <div class="row mb-4">
      <div class="col-12 col-md-8 mx-auto">
        <div class="input-group">
          <input 
            type="text" 
            class="form-control" 
            placeholder="搜索歌单名称或关键词..." 
            v-model="searchKeyword"
            @keyup.enter="handleSearch"
          >
          <button 
            class="btn btn-primary" 
            type="button" 
            @click="handleSearch"
            :disabled="isLoading"
          >
            <i class="fas fa-search me-2"></i>
            {{ isLoading ? '搜索中...' : '搜索' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="playlists.length > 0" class="mt-4">
      <h5 class="mb-3">搜索结果 ({{ playlists.length }})</h5>
      <div class="row">
        <div v-for="playlist in playlists" :key="playlist.id" class="col-12 col-sm-6 col-md-4 col-lg-3 mb-4">
          <div class="card music-card h-100">
            <img 
              :src="playlist.coverImgUrl || playlist.picUrl" 
              :alt="playlist.name"
              class="card-img-top"
              style="height: 180px; object-fit: cover;"
              @error="handleImageError"
            >
            <div class="card-body">
              <h6 class="card-title text-truncate" :title="playlist.name">{{ playlist.name }}</h6>
              <p class="card-text small text-muted mb-2">
                <i class="fas fa-user me-1"></i>
                {{ playlist.creator || playlist.copywriter || '未知创建者' }}
              </p>
              
              <!-- 标签显示 -->
              <div v-if="playlist.tags && playlist.tags.length > 0" class="mb-2">
                <small class="text-muted">
                  <i class="fas fa-tags me-1"></i>
                  {{ playlist.tags.join(' · ') }}
                </small>
              </div>
              
              <div class="d-flex justify-content-between align-items-center mb-3">
                <small class="text-muted">
                  <i class="fas fa-play-circle me-1"></i>
                  {{ formatPlayCount(playlist.playCount) }}
                </small>
                <small class="text-muted">
                  <i class="fas fa-music me-1"></i>
                  {{ playlist.trackCount || 0 }}
                </small>
              </div>

              <!-- 下载按钮 -->
              <button 
                class="btn btn-success btn-sm w-100"
                @click="handleDownload(playlist)"
                :disabled="isPlaylistDownloading(playlist.id)"
              >
                <i class="fas fa-download me-2"></i>
                {{ isPlaylistDownloading(playlist.id) ? '下载中...' : '下载歌单' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">加载中...</span>
      </div>
      <p class="mt-2 text-muted">正在搜索歌单，请稍候...</p>
    </div>

    <!-- 空状态 -->
    <div v-if="!isLoading && playlists.length === 0 && hasSearched" class="text-center py-4">
      <i class="fas fa-search fa-3x text-muted mb-3"></i>
      <p class="text-muted">暂无搜索结果，请尝试其他关键词</p>
    </div>

    <!-- 初始提示 -->
    <div v-if="!hasSearched && !isLoading" class="text-center py-5">
      <i class="fas fa-layer-group fa-3x text-muted mb-3"></i>
      <h4 class="text-muted">歌单搜索与下载</h4>
      <p class="text-muted">输入歌单名称或关键词搜索并下载歌单</p>
    </div>

    <!-- 错误信息 -->
    <div v-if="errorMessage" class="alert alert-danger mt-3" role="alert">
      <i class="fas fa-exclamation-triangle me-2"></i>
      {{ errorMessage }}
    </div>

    <!-- 下载成功提示 -->
    <div v-if="downloadSuccess" class="alert alert-success mt-3" role="alert">
      <i class="fas fa-check-circle me-2"></i>
      歌单下载任务已开始，请查看下载进度
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import apiService from '../services/apiService.js'

export default {
  name: 'PlaylistSearchComponent',
  setup() {
    const searchKeyword = ref('')
    const playlists = ref([])
    const isLoading = ref(false)
    const hasSearched = ref(false)
    const errorMessage = ref('')
    const isDownloading = ref(false)
    const downloadSuccess = ref(false)

    // 格式化播放次数
    const formatPlayCount = (count) => {
      if (!count) return '0'
      if (count >= 10000) {
        return (count / 10000).toFixed(1) + '万'
      }
      if (count >= 100000000) {
        return (count / 100000000).toFixed(1) + '亿'
      }
      return count.toString()
    }

    // 处理图片加载错误
    const handleImageError = (event) => {
      event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuWbvueJh+WbvueJhzwvdGV4dD48L3N2Zz4='
    }

    // 处理搜索
    const handleSearch = async () => {
      if (!searchKeyword.value.trim()) {
        errorMessage.value = '请输入搜索关键词'
        return
      }

      isLoading.value = true
      errorMessage.value = ''
      playlists.value = []
      downloadSuccess.value = false

      try {
        const response = await apiService.searchMusic(searchKeyword.value, 100, 0, '1000')
        
        if (response.status === 200) {
          // 后端已排序，直接使用返回的数据
          playlists.value = response.data || []
          hasSearched.value = true
        } else {
          errorMessage.value = response.message || '搜索失败'
        }
      } catch (error) {
        console.error('搜索歌单错误:', error)
        errorMessage.value = '搜索过程中发生错误，请重试'
      } finally {
        isLoading.value = false
      }
    }

    // 为每个歌单维护下载状态
    const downloadingPlaylists = ref(new Set())

    // 处理下载
    const handleDownload = async (playlist) => {
      if (!playlist || !playlist.id) {
        errorMessage.value = '无效的歌单信息'
        return
      }

      // 检查是否已经在下载中
      if (downloadingPlaylists.value.has(playlist.id)) {
        return
      }

      // 添加到下载中集合
      downloadingPlaylists.value.add(playlist.id)
      errorMessage.value = ''
      downloadSuccess.value = false

      try {
        const response = await apiService.downloadPlaylist(playlist.id, 'lossless', true, 3, null, true)
        
        if (response.status === 200) {
          downloadSuccess.value = true
          // 3秒后自动隐藏成功提示
          setTimeout(() => {
            downloadSuccess.value = false
          }, 3000)
        } else {
          errorMessage.value = response.message || '下载失败'
        }
      } catch (error) {
        console.error('下载歌单错误:', error)
        errorMessage.value = '下载过程中发生错误，请重试'
      } finally {
        // 从下载中集合移除
        downloadingPlaylists.value.delete(playlist.id)
      }
    }

    // 检查歌单是否正在下载
    const isPlaylistDownloading = (playlistId) => {
      return downloadingPlaylists.value.has(playlistId)
    }

    return {
      searchKeyword,
      playlists,
      isLoading,
      hasSearched,
      errorMessage,
      isDownloading,
      downloadSuccess,
      formatPlayCount,
      handleImageError,
      handleSearch,
      handleDownload,
      isPlaylistDownloading
    }
  }
}
</script>

<style scoped>
.card {
  transition: all 0.3s ease;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.card-img-top {
  border-bottom: 1px solid rgba(0, 0, 0, 0.125);
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}
</style>

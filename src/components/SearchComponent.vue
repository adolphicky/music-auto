<template>
  <div>
    <div class="row">
      <div class="col-12 col-md-6">
        <div class="mb-3">
          <label for="searchKeywords" class="form-label">搜索关键词</label>
          <input 
            type="text" 
            id="searchKeywords" 
            class="form-control" 
            placeholder="输入关键词进行搜索"
            v-model="searchKeyword"
            @keyup.enter="handleSearch"
          >
        </div>
      </div>
      <div class="col-12 col-md-3">
        <div class="mb-3">
          <label for="searchLimit" class="form-label">返回数量</label>
          <input 
            type="number" 
            id="searchLimit" 
            class="form-control" 
            v-model.number="searchLimit"
            min="1" 
            placeholder="留空获取所有数据"
          >
        </div>
      </div>
      <div class="col-12 col-md-3">
        <div class="mb-3">
          <label for="searchType" class="form-label">搜索类型</label>
          <select id="searchType" class="form-select" v-model="searchType">
            <option value="1">歌曲</option>
            <option value="10">专辑</option>
            <option value="100">歌手</option>
            <option value="1000">歌单</option>
          </select>
        </div>
      </div>
    </div>

    <div class="text-center mb-4">
      <button 
        type="button" 
        class="btn btn-gradient w-50" 
        @click="handleSearch"
        :disabled="isSearching"
      >
        <i class="fas fa-search me-2"></i>
        {{ isSearching ? '搜索中...' : '搜索' }}
      </button>
    </div>

    <!-- 搜索结果 -->
    <div v-if="searchResults.length > 0" class="mt-4">
      <h5 class="mb-3">搜索结果 ({{ searchResults.length }})</h5>
      <div class="row">
        <div v-for="(song, index) in searchResults" :key="index" class="col-12 col-md-6 col-lg-4 mb-3">
          <div 
            class="card music-card h-100 position-relative"
            :style="{
              backgroundImage: `url(${getAlbumBackground(song)})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              backgroundRepeat: 'no-repeat'
            }"
          >
            <!-- 半透明遮罩 -->
            <div class="card-overlay position-absolute w-100 h-100" style="background: rgba(0,0,0,0.4);"></div>
            
            <div class="card-body position-relative text-white">
              <h6 class="card-title text-truncate" :title="song.name">{{ song.name }}</h6>
              <p class="card-text small mb-1 text-truncate" :title="song.artist_string || song.artists?.map(a => a.name).join(', ')">
                <i class="fas fa-user me-1"></i>
                {{ song.artist_string || song.artists?.map(a => a.name).join(', ') }}
              </p>
              <p class="card-text small mb-2" :title="song.album?.name || '未知专辑'">
                <i class="fas fa-compact-disc me-1"></i>
                {{ song.album?.name || '未知专辑' }}
              </p>
              <div class="d-flex justify-content-between align-items-center">
                <small>{{ formatDuration(song.duration) }}</small>
                <div>
                  <button 
                    class="btn btn-sm btn-outline-light me-1"
                    @click="handleParse(song.id)"
                    title="解析歌曲"
                  >
                    <i class="fas fa-info-circle"></i>
                  </button>
                  <button 
                    class="btn btn-sm btn-outline-light"
                    @click="handleDownload(song.id)"
                    title="下载歌曲"
                  >
                    <i class="fas fa-download"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="isSearching" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">加载中...</span>
      </div>
      <p class="mt-2 text-muted">正在搜索中，请稍候...</p>
    </div>

    <!-- 空状态 -->
    <div v-if="!isSearching && searchResults.length === 0 && hasSearched" class="text-center py-4">
      <i class="fas fa-search fa-3x text-muted mb-3"></i>
      <p class="text-muted">暂无搜索结果，请尝试其他关键词</p>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import apiService from '../services/apiService.js'

export default {
  name: 'SearchComponent',
  setup() {
    const searchKeyword = ref('')
    const searchLimit = ref(10)
    const searchType = ref('1')
    const searchResults = ref([])
    const isSearching = ref(false)
    const hasSearched = ref(false)

    // 格式化时长
    const formatDuration = (ms) => {
      if (!ms) return '未知'
      const minutes = Math.floor(ms / 60000)
      const seconds = Math.floor((ms % 60000) / 1000)
      return `${minutes}:${seconds.toString().padStart(2, '0')}`
    }

    // 获取专辑背景图片
    const getAlbumBackground = (song) => {
      const defaultBackground = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuWbvueJh+WbvueJhzwvdGV4dD48L3N2Zz4='
      
      const imageUrl = song.album?.picUrl || song.picUrl
      
      // 如果没有图片URL，直接返回默认背景
      if (!imageUrl) {
        return defaultBackground
      }
      
      // 简单返回图片URL，让浏览器处理加载和错误
      // 如果图片加载失败，浏览器会显示默认的"损坏图片"图标
      // 我们通过CSS的background-image fallback机制来处理
      return imageUrl
    }

    // 处理专辑图片加载错误（保留用于其他用途）
    const handleAlbumImageError = (event) => {
      event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjUiIGhlaWdodD0iMjUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iI2RkZCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iNiIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuWbvueJhzwvdGV4dD48L3N2Zz4='
    }

    // 处理搜索
    const handleSearch = async () => {
      if (!searchKeyword.value.trim()) {
        alert('请输入搜索关键词')
        return
      }

      isSearching.value = true
      hasSearched.value = true

      try {
        const response = await apiService.searchMusic(
          searchKeyword.value,
          searchLimit.value,
          0,
          searchType.value
        )
        
        if (response.status === 200) {
          searchResults.value = response.data || []
        } else {
          alert('搜索失败: ' + (response.message || '未知错误'))
          searchResults.value = []
        }
      } catch (error) {
        console.error('搜索错误:', error)
        alert('搜索过程中发生错误，请重试')
        searchResults.value = []
      } finally {
        isSearching.value = false
      }
    }

    // 处理解析
    const handleParse = (songId) => {
      // 切换到解析标签页并传递歌曲ID
      // 这里需要与父组件通信，暂时先显示提示
      alert(`准备解析歌曲ID: ${songId}`)
    }

    // 处理下载
    const handleDownload = async (songId) => {
      try {
        // 调用下载API
        const response = await apiService.downloadMusic(songId, 'lossless', 'json')
        
        if (response.status === 200) {
          // 下载成功
          const songInfo = response.data
          alert(`下载成功！\n歌曲: ${songInfo.name}\n歌手: ${songInfo.artist}\n文件路径: ${songInfo.file_path}`)
        } else {
          // 下载失败
          alert(`下载失败: ${response.message || '未知错误'}`)
        }
      } catch (error) {
        console.error('下载错误:', error)
        alert('下载过程中发生错误，请重试')
      }
    }

    return {
      searchKeyword,
      searchLimit,
      searchType,
      searchResults,
      isSearching,
      hasSearched,
      formatDuration,
      getAlbumBackground,
      handleAlbumImageError,
      handleSearch,
      handleParse,
      handleDownload
    }
  }
}
</script>

<style scoped>
.card {
  transition: all 0.3s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}
</style>

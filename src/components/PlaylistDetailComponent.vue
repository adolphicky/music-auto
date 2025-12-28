<template>
  <div>
    <!-- 返回按钮 -->
    <div class="mb-4">
      <button class="btn btn-outline-secondary" @click="goBack">
        <i class="fas fa-arrow-left me-2"></i>
        返回热门歌单
      </button>
    </div>

    <!-- 歌单信息 -->
    <div v-if="playlist" class="card mb-4">
      <div class="row g-0">
        <div class="col-md-3">
          <img 
            :src="playlist.coverImgUrl" 
            :alt="playlist.name"
            class="img-fluid rounded-start"
            style="height: 200px; object-fit: cover;"
            @error="handleImageError"
          >
        </div>
        <div class="col-md-9">
          <div class="card-body">
            <h3 class="card-title">{{ playlist.name }}</h3>
            <p class="card-text">
              <i class="fas fa-user me-2"></i>
              创建者: {{ playlist.creator?.nickname || '未知' }}
            </p>
            <p class="card-text">
              <i class="fas fa-play-circle me-2"></i>
              播放次数: {{ formatPlayCount(playlist.playCount) }}
            </p>
            <p class="card-text">
              <i class="fas fa-music me-2"></i>
              歌曲数量: {{ playlist.trackCount || 0 }} 首
            </p>
            <p class="card-text" v-if="playlist.description">
              <i class="fas fa-info-circle me-2"></i>
              描述: {{ playlist.description }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 歌曲列表 -->
    <div v-if="songs.length > 0" class="mt-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5>歌曲列表 ({{ songs.length }})</h5>
        <div class="d-flex align-items-center">
          <span class="me-2">每页显示:</span>
          <select v-model="pageSize" class="form-select form-select-sm" style="width: auto;">
            <option value="20">20</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </div>
      </div>

      <!-- 分页控件 -->
      <div v-if="totalPages > 1" class="d-flex justify-content-between align-items-center mb-3">
        <div>
          第 {{ currentPage }} 页，共 {{ totalPages }} 页
        </div>
        <nav>
          <ul class="pagination pagination-sm mb-0">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <button class="page-link" @click="changePage(currentPage - 1)">上一页</button>
            </li>
            <li v-for="page in visiblePages" :key="page" class="page-item" :class="{ active: page === currentPage }">
              <button class="page-link" @click="changePage(page)">{{ page }}</button>
            </li>
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <button class="page-link" @click="changePage(currentPage + 1)">下一页</button>
            </li>
          </ul>
        </nav>
      </div>

      <!-- 批量下载操作栏 -->
      <div v-if="songs.length > 0" class="d-flex justify-content-between align-items-center mb-3">
        <h5>歌曲列表 ({{ songs.length }})</h5>
        <div class="d-flex gap-2">
          <div class="form-check">
            <input 
              type="checkbox" 
              id="selectAll" 
              class="form-check-input" 
              v-model="selectAll"
              @change="toggleSelectAll"
            >
            <label for="selectAll" class="form-check-label">全选</label>
          </div>
          <button 
            class="btn btn-sm btn-success"
            @click="downloadSelected"
            :disabled="selectedSongs.length === 0 || isDownloading"
          >
            <i class="fas fa-download me-1"></i>
            下载选中 ({{ selectedSongs.length }})
          </button>
          <button 
            class="btn btn-sm btn-info"
            @click="downloadAll"
            :disabled="songs.length === 0 || isDownloading"
          >
            <i class="fas fa-download me-1"></i>
            下载全部
          </button>
        </div>
      </div>

      <!-- 歌曲表格 -->
      <div class="table-responsive">
        <table class="table table-hover">
          <thead>
            <tr>
              <th width="40">
                <input 
                  type="checkbox" 
                  v-model="selectAll"
                  @change="toggleSelectAll"
                >
              </th>
              <th scope="col" style="width: 50px;">#</th>
              <th scope="col">歌曲名称</th>
              <th scope="col">歌手</th>
              <th scope="col">专辑</th>
              <th scope="col">时长</th>
              <th scope="col" style="width: 120px;">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(song, index) in paginatedSongs" :key="song.id">
              <td>
                <input 
                  type="checkbox" 
                  v-model="selectedSongs"
                  :value="song.id"
                >
              </td>
              <td>{{ (currentPage - 1) * pageSize + index + 1 }}</td>
              <td class="text-truncate" :title="song.name">{{ song.name }}</td>
              <td class="text-truncate" :title="song.ar ? song.ar.map(artist => artist.name).join('/') : '未知歌手'">
                {{ song.ar ? song.ar.map(artist => artist.name).join('/') : '未知歌手' }}
              </td>
              <td>
                <div class="d-flex align-items-center">
                  <img 
                    v-if="song.al?.picUrl" 
                    :src="song.al.picUrl" 
                    :alt="song.al.name"
                    class="me-2 rounded"
                    style="width: 30px; height: 30px; object-fit: cover;"
                    @error="handleAlbumImageError"
                  >
                  <span class="text-truncate" :title="song.al?.name || '未知专辑'">
                    {{ song.al?.name || '未知专辑' }}
                  </span>
                </div>
              </td>
              <td>{{ formatDuration(song.dt) }}</td>
              <td>
                <button 
                  class="btn btn-sm btn-outline-success"
                  @click="downloadSingle(song.id)"
                  :disabled="isDownloading"
                  title="下载歌曲"
                >
                  <i class="fas fa-download"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 底部分页控件 -->
      <div v-if="totalPages > 1" class="d-flex justify-content-center mt-3">
        <nav>
          <ul class="pagination">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <button class="page-link" @click="changePage(currentPage - 1)">上一页</button>
            </li>
            <li v-for="page in visiblePages" :key="page" class="page-item" :class="{ active: page === currentPage }">
              <button class="page-link" @click="changePage(page)">{{ page }}</button>
            </li>
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <button class="page-link" @click="changePage(currentPage + 1)">下一页</button>
            </li>
          </ul>
        </nav>
      </div>
    </div>

    <!-- 下载进度 -->
    <div v-if="isDownloading" class="mt-3">
      <div class="progress">
        <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 100%"></div>
      </div>
      <div class="text-center mt-2">
        <small class="text-muted">{{ downloadMessage }}</small>
      </div>
    </div>

    <!-- 下载结果 -->
    <div v-if="downloadResults.length > 0" class="mt-4">
      <h6>下载结果</h6>
      <div class="card">
        <div class="card-body">
          <div v-for="(result, index) in downloadResults" :key="index" 
               :class="result.success ? 'alert alert-success' : 'alert alert-danger'" 
               role="alert">
            <i :class="result.success ? 'fas fa-check-circle' : 'fas fa-exclamation-triangle'" class="me-2"></i>
            {{ result.message }}
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">加载中...</span>
      </div>
      <p class="mt-2 text-muted">正在加载歌单详情，请稍候...</p>
    </div>

    <!-- 空状态 -->
    <div v-if="!isLoading && songs.length === 0 && hasLoaded" class="text-center py-4">
      <i class="fas fa-music fa-3x text-muted mb-3"></i>
      <p class="text-muted">暂无歌曲数据</p>
    </div>

    <!-- 错误信息 -->
    <div v-if="errorMessage" class="alert alert-danger mt-3" role="alert">
      <i class="fas fa-exclamation-triangle me-2"></i>
      {{ errorMessage }}
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import apiService from '../services/apiService.js'

export default {
  name: 'PlaylistDetailComponent',
  props: {
    playlist: {
      type: Object,
      required: true
    }
  },
  setup(props, context) {
    const songs = ref([])
    const isLoading = ref(false)
    const hasLoaded = ref(false)
    const errorMessage = ref('')
    const currentPage = ref(1)
    const pageSize = ref(20) // 默认显示50首
    
    // 下载相关状态
    const isDownloading = ref(false)
    const downloadMessage = ref('正在下载...')
    const downloadResults = ref([])
    
    // 批量下载状态
    const selectedSongs = ref([])
    const selectAll = ref(false)

    // 计算属性
    const totalPages = computed(() => {
      return Math.ceil(songs.value.length / pageSize.value)
    })

    const paginatedSongs = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      return songs.value.slice(start, end)
    })

    const visiblePages = computed(() => {
      const pages = []
      const maxVisible = 5
      let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
      let end = Math.min(totalPages.value, start + maxVisible - 1)
      
      if (end - start + 1 < maxVisible) {
        start = Math.max(1, end - maxVisible + 1)
      }
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      return pages
    })

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

    // 格式化时长
    const formatDuration = (ms) => {
      if (!ms) return '00:00'
      const minutes = Math.floor(ms / 60000)
      const seconds = Math.floor((ms % 60000) / 1000)
      return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    }

    // 处理图片加载错误
    const handleImageError = (event) => {
      event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuWbvueJh+WbvueJhzwvdGV4dD48L3N2Zz4='
    }

    // 处理专辑图片加载错误
    const handleAlbumImageError = (event) => {
      event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAiIGhlaWdodD0iMzAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iI2RkZCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuWbvueJhzwvdGV4dD48L3N2Zz4='
    }

    // 获取歌单详情
    const fetchPlaylistDetail = async () => {
      isLoading.value = true
      errorMessage.value = ''
      songs.value = []

      try {
        const response = await apiService.getPlaylist(props.playlist.id)
        
        if (response.status === 200) {
          songs.value = response.data?.playlist?.tracks || []
          hasLoaded.value = true
        } else {
          errorMessage.value = response.message || '获取歌单详情失败'
        }
      } catch (error) {
        console.error('获取歌单详情错误:', error)
        errorMessage.value = '获取过程中发生错误，请重试'
      } finally {
        isLoading.value = false
      }
    }

    // 切换页面
    const changePage = (page) => {
      if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page
      }
    }

    // 返回热门歌单
    const goBack = () => {
      // 触发back事件通知父组件返回歌单列表
      context.emit('back')
    }

    // 监听pageSize变化，重置到第一页
    const watchPageSize = () => {
      currentPage.value = 1
    }

    // 全选/取消全选
    const toggleSelectAll = () => {
      if (selectAll.value) {
        selectedSongs.value = paginatedSongs.value.map(song => song.id)
      } else {
        selectedSongs.value = []
      }
    }

    // 下载选中歌曲
    const downloadSelected = async () => {
      if (selectedSongs.value.length === 0) {
        errorMessage.value = '请先选择要下载的歌曲'
        return
      }
      await downloadPlaylist('选中歌曲下载', selectedSongs.value)
    }

    // 下载全部歌曲
    const downloadAll = async () => {
      if (songs.value.length === 0) {
        errorMessage.value = '没有可下载的歌曲'
        return
      }
      await downloadPlaylist('全部歌曲下载', songs.value.map(song => song.id))
    }

    // 下载单首歌曲
    const downloadSingle = async (songId) => {
      await downloadSongs([songId], '单曲下载')
    }

    // 歌单下载
    const downloadPlaylist = async (operationName, selectedSongIds = null) => {
      isDownloading.value = true
      errorMessage.value = ''
      downloadResults.value = []
      downloadMessage.value = `${operationName}中...`

      try {
        const response = await apiService.downloadPlaylist(
          props.playlist.id, 
          'lossless', 
          true, 
          3,
          selectedSongIds  // 传递选中的歌曲ID列表
        )
        
        if (response.status === 200) {
          downloadResults.value = [{
            success: true,
            message: `${operationName}完成！${response.message || '下载成功'}`
          }]
        } else {
          downloadResults.value = [{
            success: false,
            message: response.message || '下载失败'
          }]
        }
      } catch (error) {
        console.error('歌单下载错误:', error)
        downloadResults.value = [{
          success: false,
          message: '下载过程中发生错误，请重试'
        }]
      } finally {
        isDownloading.value = false
        downloadMessage.value = '正在下载...'
      }
    }

    // 批量下载歌曲（用于单曲下载）
    const downloadSongs = async (songIds, operationName) => {
      isDownloading.value = true
      errorMessage.value = ''
      downloadResults.value = []
      downloadMessage.value = `${operationName}中...`

      try {
        const results = []
        let successCount = 0
        let failCount = 0
        const failedSongs = []

        for (let i = 0; i < songIds.length; i++) {
          const songId = songIds[i]
          downloadMessage.value = `${operationName}中... (${i + 1}/${songIds.length})`
          
          try {
            const response = await apiService.downloadMusic(songId, 'lossless', 'json')
            
            if (response.status === 200) {
              results.push({
                success: true,
                message: `下载成功: ${response.data.name} - ${response.data.artist}`
              })
              successCount++
            } else {
              failedSongs.push({
                id: songId,
                message: response.message || '未知错误'
              })
              failCount++
            }
          } catch (error) {
            failedSongs.push({
              id: songId,
              message: error.message
            })
            failCount++
          }
        }

        // 添加成功结果
        if (successCount > 0) {
          results.push({
            success: true,
            message: `成功下载 ${successCount} 首歌曲`
          })
        }

        // 添加失败结果（汇总显示）
        if (failCount > 0) {
          if (failCount <= 3) {
            // 失败数量较少时，显示详细信息
            failedSongs.forEach(failedSong => {
              results.push({
                success: false,
                message: `下载失败: ${failedSong.message}`
              })
            })
          } else {
            // 失败数量较多时，汇总显示
            results.push({
              success: false,
              message: `有 ${failCount} 首歌曲下载失败`
            })
          }
        }

        // 添加总结信息
        results.push({
          success: true,
          message: `${operationName}完成！成功: ${successCount}首，失败: ${failCount}首`
        })

        downloadResults.value = results
      } catch (error) {
        console.error('批量下载错误:', error)
        errorMessage.value = '下载过程中发生错误，请重试'
      } finally {
        isDownloading.value = false
        downloadMessage.value = '正在下载...'
      }
    }

    // 组件挂载时获取数据
    onMounted(() => {
      fetchPlaylistDetail()
    })

    return {
      songs,
      isLoading,
      hasLoaded,
      errorMessage,
      currentPage,
      pageSize,
      totalPages,
      paginatedSongs,
      visiblePages,
      formatPlayCount,
      formatDuration,
      handleImageError,
      handleAlbumImageError,
      changePage,
      goBack,
      watchPageSize,
      // 下载相关
      isDownloading,
      downloadMessage,
      downloadResults,
      downloadSingle,
      downloadSongs,
      // 批量下载相关
      selectedSongs,
      selectAll,
      toggleSelectAll,
      downloadSelected,
      downloadAll
    }
  }
}
</script>

<style scoped>
.table th {
  border-top: none;
  font-weight: 600;
}

.table tbody tr:hover {
  background-color: rgba(0, 123, 255, 0.05);
}

.pagination {
  margin-bottom: 0;
}

.card {
  transition: all 0.3s ease;
}
</style>

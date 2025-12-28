<template>
  <div>
    <!-- 歌手搜索区域 -->
    <div class="row">
      <div class="col-12 col-md-6">
        <div class="mb-3">
          <label for="artist_download_name" class="form-label">歌手名称</label>
          <input 
            type="text" 
            id="artist_download_name" 
            class="form-control" 
            placeholder="输入歌手名称（如：周深、林俊杰）"
            v-model="artistName"
            @keyup.enter="searchArtistSongs"
          >
        </div>
      </div>
      <div class="col-12 col-md-3">
        <div class="mb-3">
          <label for="artist_download_quality" class="form-label">下载音质</label>
          <select id="artist_download_quality" class="form-select" v-model="selectedQuality">
            <option value="standard">标准音质</option>
            <option value="exhigh">极高音质</option>
            <option value="lossless" selected>无损音质</option>
            <option value="hires">Hires音质</option>
            <option value="sky">沉浸环绕声</option>
            <option value="jyeffect">高清环绕声</option>
            <option value="jymaster">超清母带</option>
          </select>
        </div>
      </div>
      <div class="col-12 col-md-3">
        <div class="mb-3">
          <label for="artist_download_pagesize" class="form-label">每页显示</label>
          <select id="artist_download_pagesize" class="form-select" v-model.number="pageSize">
            <option value="20">20首</option>
            <option value="50" selected>50首</option>
            <option value="100">100首</option>
          </select>
        </div>
      </div>
    </div>

    <div class="text-center mb-4">
      <button 
        type="button" 
        class="btn btn-primary w-50" 
        @click="searchArtistSongs"
        :disabled="isSearching"
      >
        <i class="fas fa-search me-2"></i>
        {{ isSearching ? '搜索中...' : '搜索歌手歌曲' }}
      </button>
    </div>

    <!-- 歌曲列表 -->
    <div v-if="songs.length > 0" class="mt-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5>歌手歌曲列表 ({{ totalSongs }}首)</h5>
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
              <th width="60">序号</th>
              <th>歌曲名称</th>
              <th>专辑</th>
              <th width="100">时长</th>
              <th width="120">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(song, index) in songs" :key="song.id">
              <td>
                <input 
                  type="checkbox" 
                  v-model="selectedSongs"
                  :value="song.id"
                >
              </td>
              <td>{{ getSongIndex(index) }}</td>
              <td>
                <div class="text-truncate" :title="song.name">{{ song.name }}</div>
                <small class="text-muted d-block text-truncate" :title="song.artist_string || song.ar?.map(a => a.name).join(', ') || '未知歌手'">
                  {{ song.artist_string || song.ar?.map(a => a.name).join(', ') || '未知歌手' }}
                </small>
              </td>
              <td>
                <div class="d-flex align-items-center">
                  <img 
                    v-if="song.album?.picUrl || song.picUrl" 
                    :src="song.album?.picUrl || song.picUrl" 
                    :alt="song.album?.name || '专辑封面'"
                    class="me-2 rounded"
                    style="width: 25px; height: 25px; object-fit: cover;"
                    @error="handleAlbumImageError"
                  >
                  <span class="text-truncate" :title="song.album?.name">
                    {{ song.album?.name || '未知专辑' }}
                  </span>
                </div>
              </td>
              <td>{{ formatDuration(song.duration || song.dt) }}</td>
              <td>
                <button 
                  class="btn btn-sm btn-outline-success"
                  @click="downloadSingle(song.id)"
                  :disabled="isDownloading"
                  title="下载单曲"
                >
                  <i class="fas fa-download"></i>
                </button>
                <button 
                  class="btn btn-sm btn-outline-primary ms-1"
                  @click="parseSong(song.id)"
                  title="解析歌曲"
                >
                  <i class="fas fa-info-circle"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页控件 -->
      <nav v-if="totalPages > 1" class="mt-4">
        <ul class="pagination justify-content-center">
          <li class="page-item" :class="{ disabled: currentPage === 1 }">
            <button class="page-link" @click="changePage(currentPage - 1)" :disabled="currentPage === 1">
              上一页
            </button>
          </li>
          
          <li v-for="page in visiblePages" :key="page" class="page-item" :class="{ active: page === currentPage }">
            <button class="page-link" @click="changePage(page)">
              {{ page }}
            </button>
          </li>
          
          <li class="page-item" :class="{ disabled: currentPage === totalPages }">
            <button class="page-link" @click="changePage(currentPage + 1)" :disabled="currentPage === totalPages">
              下一页
            </button>
          </li>
        </ul>
        <div class="text-center text-muted small">
          第 {{ Number(currentPage) || 1 }} 页，共 {{ totalPages }} 页，总计 {{ totalSongs }} 首歌曲
        </div>
      </nav>
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
    <div v-if="isSearching" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">加载中...</span>
      </div>
      <p class="mt-2 text-muted">正在搜索歌手歌曲，请稍候...</p>
    </div>

    <!-- 空状态 -->
    <div v-if="!isSearching && songs.length === 0 && hasSearched" class="text-center py-4">
      <i class="fas fa-music fa-3x text-muted mb-3"></i>
      <p class="text-muted">暂无歌曲数据，请先搜索歌手</p>
    </div>

    <!-- 错误信息 -->
    <div v-if="errorMessage" class="alert alert-danger mt-3" role="alert">
      <i class="fas fa-exclamation-triangle me-2"></i>
      {{ errorMessage }}
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import apiService from '../services/apiService.js'

export default {
  name: 'ArtistDownloadComponent',
  setup() {
    const artistName = ref('')
    const selectedQuality = ref('lossless')
    const pageSize = ref(50)  // 增加默认每页大小到100
    const currentPage = ref(1)
    const totalSongs = ref(0)
    const totalPages = ref(0)
    const songs = ref([])
    const selectedSongs = ref([])
    const selectAll = ref(false)
    
    const isSearching = ref(false)
    const isDownloading = ref(false)
    const hasSearched = ref(false)
    const errorMessage = ref('')
    const downloadMessage = ref('正在下载...')
    const downloadResults = ref([])

    // 计算可见页码
    const visiblePages = computed(() => {
      const pages = []
      const maxVisiblePages = 5
      let startPage = Math.max(1, currentPage.value - Math.floor(maxVisiblePages / 2))
      let endPage = startPage + maxVisiblePages - 1
      
      if (endPage > totalPages.value) {
        endPage = totalPages.value
        startPage = Math.max(1, endPage - maxVisiblePages + 1)
      }
      
      for (let i = startPage; i <= endPage; i++) {
        pages.push(i)
      }
      return pages
    })

    // 格式化时长
    const formatDuration = (ms) => {
      if (!ms) return '未知'
      const minutes = Math.floor(ms / 60000)
      const seconds = Math.floor((ms % 60000) / 1000)
      return `${minutes}:${seconds.toString().padStart(2, '0')}`
    }

    // 处理专辑图片加载错误
    const handleAlbumImageError = (event) => {
      event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjUiIGhlaWdodD0iMjUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iI2RkZCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iNiIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuWbvueJhzwvdGV4dD48L3N2Zz4='
    }

    // 搜索歌手歌曲
    const searchArtistSongs = async (page = 1) => {
        if (!artistName.value.trim()) {
            errorMessage.value = '请输入歌手名称'
            return
        }

        isSearching.value = true
        errorMessage.value = ''
        songs.value = []
        // 不再清空selectedSongs，支持跨页选中
        selectAll.value = false
        downloadResults.value = []
        
        // 确保page是有效数字
        const pageNum = Number(page)
        currentPage.value = isNaN(pageNum) ? 1 : Math.max(1, pageNum)

        try {
            // 使用搜索API获取歌手歌曲（不限制数量，使用分页）
            const offset = (currentPage.value - 1) * pageSize.value
            const response = await apiService.searchMusic(
                artistName.value,
                pageSize.value,
                offset,
                '1'  // 搜索类型：歌曲（搜索歌手名来获取该歌手的歌曲）
            )
            
            if (response.success) {
                songs.value = response.data || []
                hasSearched.value = true
                
                // 使用后端返回的总数信息
                console.log('API Response:', response)
                totalSongs.value = response.total || (response.data ? response.data.length : 0)
                totalPages.value = Math.max(1, Math.ceil(totalSongs.value / pageSize.value))
                console.log('Total songs:', totalSongs.value, 'Total pages:', totalPages.value, 'Current page:', currentPage.value)
            } else {
                errorMessage.value = response.message || '搜索失败'
            }
        } catch (error) {
            console.error('搜索歌手歌曲错误:', error)
            errorMessage.value = '搜索过程中发生错误，请重试'
        } finally {
            isSearching.value = false
        }
    }

    // 切换页码
    const changePage = (page) => {
      console.log('changePage called with:', page, 'type:', typeof page)
      
      // 处理可能的事件对象字符串拼接问题
      let pageNum
      
      // 如果是字符串，检查是否包含事件对象
      if (typeof page === 'string') {
        // 检查是否包含"[object"字样，说明是事件对象字符串
        if (page.includes('[object')) {
          console.warn('Received event object string:', page)
          // 尝试提取数字部分
          const match = page.match(/\d+/)
          if (match) {
            pageNum = Number(match[0])
            console.log('Extracted page number from event string:', pageNum)
          } else {
            console.error('Could not extract page number from:', page)
            return
          }
        } else {
          // 正常字符串数字
          pageNum = Number(page)
        }
      } else if (typeof page === 'number') {
        // 直接是数字
        pageNum = page
      } else if (page && typeof page === 'object' && (page.target || page.preventDefault)) {
        // 事件对象
        console.warn('Received event object, ignoring')
        return
      } else {
        console.error('Invalid page parameter:', page)
        return
      }
      
      // 检查是否为有效数字
      if (isNaN(pageNum)) {
        console.error('Invalid page number:', pageNum)
        return
      }
      
      // 检查页码范围
      if (pageNum >= 1 && pageNum <= totalPages.value) {
        console.log('Changing to page:', pageNum)
        searchArtistSongs(pageNum)
      } else {
        console.log('Page out of range:', pageNum, 'valid range: 1 to', totalPages.value)
      }
    }

    // 全选/取消全选
    const toggleSelectAll = () => {
      if (selectAll.value) {
        selectedSongs.value = songs.value.map(song => song.id)
      } else {
        selectedSongs.value = []
      }
    }

    // 监听选中歌曲变化，更新全选状态
    watch(selectedSongs, (newVal) => {
      selectAll.value = newVal.length === songs.value.length && songs.value.length > 0
    })

    // 监听pageSize变化，自动刷新页面
    watch(pageSize, (newSize, oldSize) => {
      // 只有当已经搜索过且pageSize确实改变时才刷新
      if (hasSearched.value && newSize !== oldSize) {
        console.log(`每页显示数量从 ${oldSize} 改为 ${newSize}，自动刷新页面`)
        // 重置到第一页并重新搜索
        currentPage.value = 1
        searchArtistSongs(1)
      }
    })

    // 下载单首歌曲
    const downloadSingle = async (songId) => {
      await downloadSongs([songId], '单曲下载')
    }

    // 下载选中歌曲
    const downloadSelected = async () => {
      if (selectedSongs.value.length === 0) {
        errorMessage.value = '请先选择要下载的歌曲'
        return
      }
      await downloadSongs(selectedSongs.value, '选中歌曲下载')
    }

    // 下载全部歌曲（所有页面的歌曲）
    const downloadAll = async () => {
      if (totalSongs.value === 0) {
        errorMessage.value = '没有可下载的歌曲'
        return
      }
      
      const confirmDownload = confirm(`确定要下载歌手 "${artistName.value}" 的所有 ${totalSongs.value} 首歌曲吗？\n\n这将使用批量下载功能，可能需要较长时间。`)
      
      if (!confirmDownload) {
        return
      }

      isDownloading.value = true
      errorMessage.value = ''
      downloadResults.value = []
      downloadMessage.value = '批量下载歌手歌曲中...'

      try {
        // 使用专门的歌手批量下载API
        const response = await apiService.downloadArtistSongs(
          artistName.value,
          selectedQuality.value,
          totalSongs.value,  // 下载所有歌曲
          'exact_single',    // 精确匹配单个歌手
          true,              // 包含歌词
          3                  // 最大并发数
        )
        
        if (response.success) {
          // 批量下载API返回的结果处理
          if (response.data && Array.isArray(response.data)) {
            response.data.forEach(result => {
              downloadResults.value.push({
                success: result.success || true,
                message: result.message || '下载完成'
              })
            })
          } else {
            downloadResults.value.push({
              success: true,
              message: `批量下载完成！总计: ${totalSongs.value}首歌曲`
            })
          }
        } else {
          downloadResults.value.push({
            success: false,
            message: response.message || '批量下载失败'
          })
        }
      } catch (error) {
        console.error('批量下载歌手歌曲错误:', error)
        downloadResults.value.push({
          success: false,
          message: `下载过程中发生错误: ${error.message}`
        })
      } finally {
        isDownloading.value = false
        downloadMessage.value = '正在下载...'
      }
    }

    // 批量下载歌曲
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
            const response = await apiService.downloadMusic(songId, selectedQuality.value, 'json')
            
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

    // 解析歌曲信息
    const parseSong = (songId) => {
      // 这里可以切换到解析标签页或显示歌曲详情
      alert(`准备解析歌曲ID: ${songId}`)
    }

    // 安全的序号计算函数
    const getSongIndex = (index) => {
      try {
        // 确保所有参数都是有效数字
        const pageNum = Number(currentPage.value) || 1
        const sizeNum = Number(pageSize.value) || 50
        const indexNum = Number(index) || 0
        
        // 计算序号
        const songIndex = (pageNum - 1) * sizeNum + indexNum + 1
        
        // 确保结果是有效数字
        return isNaN(songIndex) ? indexNum + 1 : songIndex
      } catch (error) {
        console.error('序号计算错误:', error)
        return index + 1  // 返回简单的索引+1作为后备
      }
    }

    return {
      artistName,
      selectedQuality,
      pageSize,
      currentPage,
      totalSongs,
      totalPages,
      songs,
      selectedSongs,
      selectAll,
      isSearching,
      isDownloading,
      hasSearched,
      errorMessage,
      downloadMessage,
      downloadResults,
      visiblePages,
      formatDuration,
      handleAlbumImageError,
      searchArtistSongs,
      changePage,
      toggleSelectAll,
      downloadSingle,
      downloadSelected,
      downloadAll,
      parseSong,
      getSongIndex
    }
  }
}
</script>

<style scoped>
.progress {
  height: 20px;
}

.table th, .table td {
  vertical-align: middle;
}

/* 优化表格容器高度，使用视口高度单位 */
.table-responsive {
  max-height: 65vh;  /* 使用视口高度的65% */
  min-height: 300px; /* 最小高度确保在小屏幕上也有足够空间 */
  overflow-y: auto;
}

.table th {
  background-color: #f8f9fa;
  position: sticky;
  top: 0;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.text-truncate {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pagination {
  margin-bottom: 0.5rem;
}

/* 优化整体布局，减少不必要的空白 */
.row {
  margin-bottom: 0.5rem; /* 减少行间距 */
}

.mb-3 {
  margin-bottom: 0.75rem !important; /* 减少表单控件间距 */
}

.mt-4 {
  margin-top: 1rem !important; /* 减少顶部间距 */
}

/* 优化卡片和容器间距 */
.card {
  margin-top: 0.5rem;
}

/* 响应式设计优化 */
@media (max-height: 768px) {
  .table-responsive {
    max-height: 45vh; /* 在小高度屏幕上使用55%视口高度 */
  }
}

@media (min-height: 900px) {
  .table-responsive {
    max-height: 55vh; /* 在大高度屏幕上使用65%视口高度 */
  }
}
</style>

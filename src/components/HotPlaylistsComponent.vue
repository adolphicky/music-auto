<template>
  <div>
    <!-- 歌单详情视图 -->
    <div v-if="selectedPlaylist">
      <PlaylistDetailComponent 
        :playlist="selectedPlaylist"
        @back="handleBackToList"
      />
    </div>

    <!-- 热门歌单列表视图 -->
    <div v-else>
      <div class="row">
        <!-- 歌单类型选择 -->
        <div class="col-12 col-md-4">
          <div class="mb-3">
            <label for="playlistType" class="form-label">歌单类型</label>
            <select id="playlistType" class="form-select" v-model="selectedType">
              <option value="personalized">推荐歌单</option>
              <option value="categories">分类歌单</option>
            </select>
          </div>
        </div>
        
        <!-- 分类歌单的独立标签选择 -->
        <div class="col-12" v-if="selectedType === 'categories'">
          <!-- 当前选择的标签 -->
          <div class="mb-3">
            <label class="form-label">已选标签</label>
            <div class="d-flex flex-wrap gap-2 mb-3">
              <span v-if="selectedTags.length === 0" class="text-muted">暂无选择</span>
              <span v-else v-for="tag in selectedTags" :key="tag" class="badge bg-primary d-flex align-items-center">
                {{ tag }}
                <button type="button" class="btn-close btn-close-white ms-2" @click="removeTag(tag)" style="font-size: 0.7rem;"></button>
              </span>
            </div>
          </div>
          
          <!-- 所有标签分类 -->
          <div class="mb-3">
            <h6 class="mb-2">语种</h6>
            <div class="d-flex flex-wrap gap-2 mb-3">
              <button v-for="tag in languageTags" :key="tag" 
                      class="btn btn-outline-primary btn-sm"
                      :class="{ 'btn-primary': selectedTags.includes(tag) }"
                      @click="toggleTag(tag)">
                {{ tag }}
              </button>
            </div>
          </div>
          
          <div class="mb-3">
            <h6 class="mb-2">风格</h6>
            <div class="d-flex flex-wrap gap-2 mb-3">
              <button v-for="tag in styleTags" :key="tag" 
                      class="btn btn-outline-primary btn-sm"
                      :class="{ 'btn-primary': selectedTags.includes(tag) }"
                      @click="toggleTag(tag)">
                {{ tag }}
              </button>
            </div>
          </div>
          
          <div class="mb-3">
            <h6 class="mb-2">场景</h6>
            <div class="d-flex flex-wrap gap-2 mb-3">
              <button v-for="tag in sceneTags" :key="tag" 
                      class="btn btn-outline-primary btn-sm"
                      :class="{ 'btn-primary': selectedTags.includes(tag) }"
                      @click="toggleTag(tag)">
                {{ tag }}
              </button>
            </div>
          </div>
          
          <div class="mb-3">
            <h6 class="mb-2">情感</h6>
            <div class="d-flex flex-wrap gap-2 mb-3">
              <button v-for="tag in emotionTags" :key="tag" 
                      class="btn btn-outline-primary btn-sm"
                      :class="{ 'btn-primary': selectedTags.includes(tag) }"
                      @click="toggleTag(tag)">
                {{ tag }}
              </button>
            </div>
          </div>
          
          <div class="mb-3">
            <h6 class="mb-2">主题</h6>
            <div class="d-flex flex-wrap gap-2 mb-3">
              <button v-for="tag in themeTags" :key="tag" 
                      class="btn btn-outline-primary btn-sm"
                      :class="{ 'btn-primary': selectedTags.includes(tag) }"
                      @click="toggleTag(tag)">
                {{ tag }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="text-center mb-4">
        <button 
          type="button" 
          class="btn btn-gradient w-50" 
          @click="fetchHotPlaylists"
          :disabled="isLoading"
        >
          <i class="fas fa-fire me-2"></i>
          {{ isLoading ? '加载中...' : '获取热门歌单' }}
        </button>
      </div>

      <!-- 歌单列表 -->
      <div v-if="playlists.length > 0" class="mt-4">
        <h5 class="mb-3">热门歌单 ({{ playlists.length }})</h5>
        <div class="row">
          <div v-for="playlist in playlists" :key="playlist.id" class="col-12 col-sm-6 col-md-4 col-lg-3 mb-4">
            <div class="card music-card h-100" style="cursor: pointer;" @click="handlePlaylistClick(playlist)">
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
                
                <div class="d-flex justify-content-between align-items-center">
                  <small class="text-muted">
                    <i class="fas fa-play-circle me-1"></i>
                    {{ formatPlayCount(playlist.playCount) }}
                  </small>
                  <small class="text-muted">
                    <i class="fas fa-music me-1"></i>
                    {{ playlist.trackCount || 0 }}
                  </small>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 分页控件 -->
        <div v-if="totalPlaylists.length > pageSize" class="mt-4">
          <nav aria-label="歌单分页">
            <ul class="pagination justify-content-center">
              <li class="page-item" :class="{ disabled: currentPage === 1 }">
                <a class="page-link" href="#" @click.prevent="prevPage" aria-label="上一页">
                  <span aria-hidden="true">&laquo;</span>
                </a>
              </li>
              
              <!-- 页码按钮 -->
              <li v-for="page in getPageNumbers()" :key="page" 
                  class="page-item" :class="{ active: page === currentPage }">
                <a class="page-link" href="#" @click.prevent="goToPage(page)">
                  {{ page }}
                </a>
              </li>
              
              <li class="page-item" :class="{ disabled: currentPage === Math.ceil(totalPlaylists.length / pageSize) }">
                <a class="page-link" href="#" @click.prevent="nextPage" aria-label="下一页">
                  <span aria-hidden="true">&raquo;</span>
                </a>
              </li>
            </ul>
          </nav>
          <div class="text-center text-muted small mt-2">
            第 {{ currentPage }} 页，共 {{ Math.ceil(totalPlaylists.length / pageSize) }} 页，
            总共 {{ totalPlaylists.length }} 个歌单
          </div>
        </div>
      </div>

      <!-- 分类歌单 -->
      <div v-if="categories.length > 0 && selectedType === 'categories'" class="mt-4">
        <h5 class="mb-3">歌单分类</h5>
        <div class="row">
          <div v-for="category in categories" :key="category.id" class="col-6 col-md-3 mb-3">
            <div class="card text-center">
              <div class="card-body">
                <h6 class="card-title">{{ category.name }}</h6>
                <p class="card-text small text-muted">{{ category.category || '歌单分类' }}</p>
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
        <p class="mt-2 text-muted">正在获取热门歌单，请稍候...</p>
      </div>

      <!-- 空状态 -->
      <div v-if="!isLoading && playlists.length === 0 && hasLoaded" class="text-center py-4">
        <i class="fas fa-music fa-3x text-muted mb-3"></i>
        <p class="text-muted">暂无歌单数据</p>
      </div>

      <!-- 错误信息 -->
      <div v-if="errorMessage" class="alert alert-danger mt-3" role="alert">
        <i class="fas fa-exclamation-triangle me-2"></i>
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import apiService from '../services/apiService.js'
import PlaylistDetailComponent from './PlaylistDetailComponent.vue'

export default {
  name: 'HotPlaylistsComponent',
  components: {
    PlaylistDetailComponent
  },
  setup() {
    const selectedType = ref('personalized')
    const selectedCategory = ref('全部')
    const playlists = ref([])
    const categories = ref([])
    const allCategories = ref([])  // 存储所有分类信息
    const isLoading = ref(false)
    const hasLoaded = ref(false)
    const errorMessage = ref('')
    const selectedPlaylist = ref(null)
    
    // 标签数据
    const languageTags = ref(['华语', '欧美', '日语', '韩语', '粤语', '小语种'])
    const styleTags = ref(['流行', '摇滚', '民谣', '电子', '说唱', '轻音乐', '爵士', '古典', '民族', '英伦', '金属', '朋克', '蓝调', '雷鬼', '世界音乐', '拉丁', 'New Age', '古风', '后摇', 'Bossa Nova'])
    const sceneTags = ref(['清晨', '夜晚', '学习', '工作', '午休', '下午茶', '地铁', '驾车', '运动', '旅行', '散步', '酒吧', '怀旧', '浪漫', '伤感', '治愈', '放松', '孤独', '感动', '兴奋', '快乐', '安静', '思念'])
    const emotionTags = ref(['怀旧', '浪漫', '伤感', '治愈', '放松', '孤独', '感动', '兴奋', '快乐', '安静', '思念'])
    const themeTags = ref(['综艺', '影视原声', 'ACG', '儿童', '校园', '游戏', '70后', '80后', '90后', '网络歌曲', 'KTV', '经典', '翻唱', '吉他', '钢琴', '器乐', '榜单', '00后'])
    
    // 已选择的标签
    const selectedTags = ref([])

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

    // 分页相关变量
    const currentPage = ref(1)
    const pageSize = ref(32)  // 每页显示32个歌单
    const totalPlaylists = ref([])  // 所有歌单数据

    // 获取完整分类信息
    const fetchAllCategories = async () => {
      try {
        const response = await apiService.getHotPlaylists('categories', '全部', 0)
        if (response.status === 200) {
          allCategories.value = response.data || []
        }
      } catch (error) {
        console.error('获取分类信息错误:', error)
      }
    }

    // 获取热门歌单
    const fetchHotPlaylists = async () => {
      isLoading.value = true
      errorMessage.value = ''
      totalPlaylists.value = []
      categories.value = []
      currentPage.value = 1  // 重置到第一页

      try {
        // 如果是分类歌单类型，先获取分类信息
        if (selectedType.value === 'categories' && allCategories.value.length === 0) {
          await fetchAllCategories()
        }

        // 传递较大的limit参数获取更多歌单
        const response = await apiService.getHotPlaylists(
          selectedType.value,
          selectedCategory.value,
          9999 // 获取9999个歌单
        )
        
        if (response.status === 200) {
          // 无论什么类型，都作为歌单列表处理
          totalPlaylists.value = response.data || []
          // 更新当前页数据
          updateCurrentPageData()
          hasLoaded.value = true
        } else {
          errorMessage.value = response.message || '获取失败'
        }
      } catch (error) {
        console.error('获取热门歌单错误:', error)
        errorMessage.value = '获取过程中发生错误，请重试'
      } finally {
        isLoading.value = false
      }
    }

    // 监听分类变化，自动获取对应分类的歌单
    watch(selectedCategory, (newCategory, oldCategory) => {
      if (selectedType.value === 'categories' && newCategory !== oldCategory) {
        console.log(`分类变化: ${oldCategory} -> ${newCategory}`)
        fetchHotPlaylists()
      }
    })

    // 监听类型变化，如果是分类歌单则获取分类信息
    const watchSelectedType = () => {
      if (selectedType.value === 'categories' && allCategories.value.length === 0) {
        fetchAllCategories()
      }
    }

    // 更新当前页数据
    const updateCurrentPageData = () => {
      const startIndex = (currentPage.value - 1) * pageSize.value
      const endIndex = startIndex + pageSize.value
      playlists.value = totalPlaylists.value.slice(startIndex, endIndex)
    }

    // 上一页
    const prevPage = () => {
      if (currentPage.value > 1) {
        currentPage.value--
        updateCurrentPageData()
      }
    }

    // 下一页
    const nextPage = () => {
      const totalPages = Math.ceil(totalPlaylists.value.length / pageSize.value)
      if (currentPage.value < totalPages) {
        currentPage.value++
        updateCurrentPageData()
      }
    }

    // 跳转到指定页
    const goToPage = (page) => {
      const totalPages = Math.ceil(totalPlaylists.value.length / pageSize.value)
      if (page >= 1 && page <= totalPages) {
        currentPage.value = page
        updateCurrentPageData()
      }
    }

    // 生成页码数组
    const getPageNumbers = () => {
      const totalPages = Math.ceil(totalPlaylists.value.length / pageSize.value)
      const current = currentPage.value
      const delta = 2  // 显示当前页前后2页
      const range = []
      
      for (let i = Math.max(2, current - delta); i <= Math.min(totalPages - 1, current + delta); i++) {
        range.push(i)
      }
      
      if (current - delta > 2) {
        range.unshift('...')
      }
      if (current + delta < totalPages - 1) {
        range.push('...')
      }
      
      range.unshift(1)
      if (totalPages > 1) {
        range.push(totalPages)
      }
      
      return range
    }

    // 处理歌单点击
    const handlePlaylistClick = (playlist) => {
      selectedPlaylist.value = playlist
    }

    // 返回歌单列表
    const handleBackToList = () => {
      selectedPlaylist.value = null
    }

    // 切换标签选择状态
    const toggleTag = (tag) => {
      const index = selectedTags.value.indexOf(tag)
      if (index > -1) {
        selectedTags.value.splice(index, 1)
      } else {
        selectedTags.value.push(tag)
      }
      updateCategorySelection()
    }

    // 移除标签
    const removeTag = (tag) => {
      const index = selectedTags.value.indexOf(tag)
      if (index > -1) {
        selectedTags.value.splice(index, 1)
        updateCategorySelection()
      }
    }

    // 更新分类选择
    const updateCategorySelection = () => {
      if (selectedTags.value.length === 0) {
        selectedCategory.value = '全部'
      } else {
        selectedCategory.value = selectedTags.value.join(' ')
      }
    }

    // 监听标签变化，自动获取对应分类的歌单
    watch(selectedTags, () => {
      if (selectedType.value === 'categories') {
        updateCategorySelection()
      }
    })

    // 监听类型变化
    watch(selectedType, (newType, oldType) => {
      if (newType === 'categories' && allCategories.value.length === 0) {
        fetchAllCategories()
      }
    })

    // 初始化加载
    fetchHotPlaylists()

    return {
      selectedType,
      selectedCategory,
      selectedTags,
      languageTags,
      styleTags,
      sceneTags,
      emotionTags,
      themeTags,
      playlists,
      categories,
      allCategories,
      isLoading,
      hasLoaded,
      errorMessage,
      selectedPlaylist,
      currentPage,
      pageSize,
      totalPlaylists,
      formatPlayCount,
      handleImageError,
      fetchHotPlaylists,
      handlePlaylistClick,
      handleBackToList,
      prevPage,
      nextPage,
      goToPage,
      getPageNumbers,
      toggleTag,
      removeTag
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

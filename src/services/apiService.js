import axios from 'axios'
import { io } from 'socket.io-client'

// 创建axios实例
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// WebSocket连接管理
class WebSocketService {
  constructor() {
    this.socket = null
    this.isConnected = false
    this.eventCallbacks = new Map()
  }

    connect() {
        if (this.socket && this.isConnected) {
            return
        }

        // 创建Socket.IO连接，指定后端服务器地址
        this.socket = io('http://localhost:5000', {
            path: '/socket.io'
        })

        this.socket.on('connect', () => {
            console.log('WebSocket连接成功')
            this.isConnected = true
            this.emitEvent('connected')
        })

        this.socket.on('disconnect', () => {
            console.log('WebSocket连接断开')
            this.isConnected = false
            this.emitEvent('disconnected')
        })

        this.socket.on('task_progress', (taskInfo) => {
            console.log('收到任务进度更新:', taskInfo)
            this.emitEvent('task_progress', taskInfo)
        })

        this.socket.on('task_error', (error) => {
            console.error('任务错误:', error)
      this.emitEvent('task_error', error)
    })

    this.socket.on('connected', (data) => {
      console.log('WebSocket连接确认:', data)
    })
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.isConnected = false
    }
  }

  subscribeTask(taskId) {
    if (this.socket && this.isConnected) {
      this.socket.emit('subscribe_task', { task_id: taskId })
    }
  }

  on(event, callback) {
    if (!this.eventCallbacks.has(event)) {
      this.eventCallbacks.set(event, [])
    }
    this.eventCallbacks.get(event).push(callback)
  }

  off(event, callback) {
    if (this.eventCallbacks.has(event)) {
      const callbacks = this.eventCallbacks.get(event)
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  emitEvent(event, data) {
    if (this.eventCallbacks.has(event)) {
      this.eventCallbacks.get(event).forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error(`WebSocket事件处理错误 (${event}):`, error)
        }
      })
    }
  }
}

// 创建WebSocket服务实例
const webSocketService = new WebSocketService()

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  async (error) => {
    console.error('API请求错误:', error)
    
    // 检查是否是cookie失效错误
    if (error.response && error.response.data && error.response.data.error_code === 'COOKIE_EXPIRED') {
      // 显示重新登录提示
      if (typeof window !== 'undefined' && window.showGlobalMessage) {
        window.showGlobalMessage('Cookie已失效，请重新扫码登录', 'error', 5000)
      }
      
      // 触发重新登录流程（由前端组件处理）
      if (typeof window !== 'undefined' && window.triggerReLogin) {
        window.triggerReLogin()
      }
    }
    
    return Promise.reject(error)
  }
)

// API服务类
class ApiService {
  // 健康检查
  async healthCheck() {
    return await apiClient.get('/health')
  }

  // 搜索音乐
  async searchMusic(keyword, limit = 30, offset = 0, type = '1') {
    return await apiClient.post('/search', {
      keyword,
      limit,
      offset,
      type
    })
  }

  // 获取歌曲信息
  async getSongInfo(songId, level = 'lossless') {
    return await apiClient.post('/song', {
      id: songId,
      level
    })
  }

  // 获取歌单详情
  async getPlaylist(playlistId) {
    return await apiClient.post('/playlist', {
      id: playlistId
    })
  }

  // 获取专辑详情
  async getAlbum(albumId) {
    return await apiClient.post('/album', {
      id: albumId
    })
  }

  // 下载音乐
  async downloadMusic(musicId, quality = 'lossless', format = 'json', asyncMode = false) {
    return await apiClient.post('/download', {
      id: musicId,
      quality,
      format,
      async: asyncMode
    })
  }

  // 歌单批量下载
  async downloadPlaylist(playlistId, quality = 'lossless', includeLyric = true, maxConcurrent = 3, selectedSongs = null, asyncMode = false) {
    const params = {
      playlist_id: playlistId,
      quality,
      include_lyric: includeLyric.toString(),  // 确保转换为字符串
      max_concurrent: maxConcurrent,
      async: asyncMode
    }
    
    // 只有当selectedSongs有值时才添加selected_songs参数
    if (selectedSongs !== null && Array.isArray(selectedSongs) && selectedSongs.length > 0) {
      params.selected_songs = selectedSongs
    }
    
    return await apiClient.post('/playlist/download', params)
  }

  // 歌手批量下载
  async downloadArtistSongs(artistName, quality = 'lossless', limit = 50, matchMode = 'exact_single', includeLyric = true, maxConcurrent = 3, asyncMode = false) {
    return await apiClient.post('/artist/download', {
      artist_name: artistName,
      quality,
      limit,
      match_mode: matchMode,
      include_lyric: includeLyric,
      max_concurrent: maxConcurrent,
      async: asyncMode
    })
  }

  // 任务管理API
  async getAllTasks() {
    return await apiClient.get('/tasks')
  }

  async getTaskInfo(taskId) {
    return await apiClient.get(`/tasks/${taskId}`)
  }

  async cancelTask(taskId) {
    return await apiClient.post(`/tasks/${taskId}/cancel`)
  }

  // 获取热门歌单
  async getHotPlaylists(type = 'personalized', category = '全部', limit = null) {
    const params = {
      type,
      category
    }
    
    // 只有当limit有值时才添加limit参数
    if (limit !== null) {
      params.limit = limit
    }
    
    return await apiClient.post('/hot/playlists', params)
  }

  // 清理已取消的任务
  async clearCancelledTasks() {
    return await apiClient.post('/tasks/clear-cancelled')
  }

  // 获取API信息
  async getApiInfo() {
    return await apiClient.get('/api/info')
  }
}

// 创建单例实例
const apiService = new ApiService()

export default apiService
export { webSocketService }

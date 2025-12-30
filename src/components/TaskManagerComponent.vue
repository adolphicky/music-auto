<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h4>任务管理</h4>
      <div>
        <button class="btn btn-outline-primary me-2" @click="refreshTasks">
          <i class="fas fa-refresh me-1"></i>刷新
        </button>
        <button class="btn btn-outline-warning me-2" @click="clearCancelledTasks">
          <i class="fas fa-ban me-1"></i>清理已取消任务
        </button>
        <button class="btn btn-outline-danger" @click="clearCompletedTasks">
          <i class="fas fa-trash me-1"></i>清理已完成任务
        </button>
      </div>
    </div>

    <!-- 任务列表 -->
    <div v-if="tasks.length > 0" class="task-list">
      <div v-for="task in tasks" :key="task.task_id" class="task-item card mb-3">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start">
            <div class="flex-grow-1">
              <h6 class="card-title mb-1">
                <span class="badge" :class="getStatusBadgeClass(task.status)">{{ getStatusText(task.status) }}</span>
                {{ getTaskDisplayName(task) }}
              </h6>
              <p class="card-text small text-muted mb-1">
                <i class="fas fa-id-card me-1"></i>任务ID: {{ task.task_id }}
              </p>
              <p class="card-text small text-muted mb-1">
                <i class="fas fa-clock me-1"></i>创建时间: {{ formatTime(task.created_at) }}
              </p>
              
              <!-- 进度条 -->
              <div v-if="task.status === 'running'" class="progress mb-2" style="height: 8px;">
                <div 
                  class="progress-bar progress-bar-striped progress-bar-animated" 
                  :style="{ width: task.progress + '%' }"
                ></div>
              </div>
              
              <div class="d-flex justify-content-between align-items-center">
                <small class="text-muted">
                  <span v-if="task.total_items > 0">
                    进度: {{ task.processed_items }}/{{ task.total_items }} ({{ task.progress.toFixed(1) }}%)
                  </span>
                  <span v-else>
                    进度: {{ task.progress.toFixed(1) }}%
                  </span>
                </small>
                
                <!-- 操作按钮 -->
                <div>
                  <button 
                    v-if="task.status === 'running' || task.status === 'pending'"
                    class="btn btn-sm btn-outline-danger"
                    @click="cancelTask(task.task_id)"
                    title="取消任务"
                  >
                    <i class="fas fa-times"></i>
                  </button>
                  <button 
                    v-if="task.error_message"
                    class="btn btn-sm btn-outline-warning ms-1"
                    @click="showError(task.error_message)"
                    title="查看错误信息"
                  >
                    <i class="fas fa-exclamation-triangle"></i>
                  </button>
                </div>
              </div>
              
              <!-- 错误信息 -->
              <div v-if="task.error_message" class="mt-2">
                <small class="text-danger">
                  <i class="fas fa-exclamation-circle me-1"></i>
                  {{ task.error_message }}
                </small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="text-center py-5">
      <i class="fas fa-tasks fa-3x text-muted mb-3"></i>
      <p class="text-muted">暂无任务</p>
    </div>

    <!-- 成功信息 -->
    <div v-if="successMessage" class="alert alert-success mt-3" role="alert">
      <i class="fas fa-check-circle me-2"></i>
      {{ successMessage }}
    </div>

    <!-- 清理已取消任务确认提示 -->
    <div v-if="showClearConfirm" class="alert alert-warning mt-3" role="alert">
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <i class="fas fa-exclamation-triangle me-2"></i>
          确定要清理所有已取消的任务吗？此操作不可撤销。
        </div>
        <div>
          <button class="btn btn-sm btn-warning me-2" @click="confirmClearCancelledTasks">
            <i class="fas fa-check me-1"></i>确认清理
          </button>
          <button class="btn btn-sm btn-secondary" @click="cancelClearCancelledTasks">
            <i class="fas fa-times me-1"></i>取消
          </button>
        </div>
      </div>
    </div>

    <!-- 清理已完成任务确认提示 -->
    <div v-if="showClearCompletedConfirm" class="alert alert-danger mt-3" role="alert">
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <i class="fas fa-exclamation-triangle me-2"></i>
          确定要清理所有已完成的任务吗？此操作不可撤销。
        </div>
        <div>
          <button class="btn btn-sm btn-danger me-2" @click="confirmClearCompletedTasks">
            <i class="fas fa-check me-1"></i>确认清理
          </button>
          <button class="btn btn-sm btn-secondary" @click="cancelClearCompletedTasks">
            <i class="fas fa-times me-1"></i>取消
          </button>
        </div>
      </div>
    </div>

    <!-- 错误信息 -->
    <div v-if="errorMessage" class="alert alert-danger mt-3" role="alert">
      <i class="fas fa-exclamation-triangle me-2"></i>
      {{ errorMessage }}
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">加载中...</span>
      </div>
      <p class="mt-2 text-muted">正在加载任务列表...</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import apiService from '../services/apiService.js'
import { webSocketService } from '../services/apiService.js'

export default {
  name: 'TaskManagerComponent',
  setup() {
    const tasks = ref([])
    const isLoading = ref(false)
    const errorMessage = ref('')
    const successMessage = ref('')

    // 排序任务列表（按创建时间倒序，最新的在最上面）
    const sortTasks = () => {
      tasks.value.sort((a, b) => b.created_at - a.created_at)
    }

    // 获取任务列表（仅用于初始加载）
    const fetchTasks = async () => {
      isLoading.value = true
      errorMessage.value = ''
      successMessage.value = ''
      try {
        const response = await apiService.getAllTasks()
        if (response.status === 200) {
          tasks.value = response.data.tasks || []
          sortTasks() // 初始加载时排序
        } else {
          console.error('获取任务列表失败:', response.message)
          errorMessage.value = '获取任务列表失败: ' + (response.message || '未知错误')
        }
      } catch (error) {
        console.error('获取任务列表错误:', error)
        errorMessage.value = '获取任务列表失败，请重试'
      } finally {
        isLoading.value = false
      }
    }

    // 更新单个任务进度
    const updateTaskProgress = (taskInfo) => {
      const taskIndex = tasks.value.findIndex(task => task.task_id === taskInfo.task_id)
      if (taskIndex !== -1) {
        // 更新现有任务
        tasks.value[taskIndex] = { ...tasks.value[taskIndex], ...taskInfo }
      } else {
        // 添加新任务
        tasks.value.push(taskInfo)
      }
      sortTasks() // 每次更新后重新排序
    }

    // 处理WebSocket连接
    const handleWebSocketConnection = () => {
      // 连接WebSocket
      webSocketService.connect()

    // 监听任务进度更新事件
    webSocketService.on('task_progress', (taskInfo) => {
        console.log('收到实时进度更新:', taskInfo)
        updateTaskProgress(taskInfo)
    })

      // 监听连接状态变化
      webSocketService.on('connected', () => {
        console.log('WebSocket已连接，重新订阅所有运行中的任务')
        // 重新订阅所有运行中的任务
        tasks.value.forEach(task => {
          if (task.status === 'running') {
            webSocketService.subscribeTask(task.task_id)
          }
        })
      })

      // 监听连接断开
      webSocketService.on('disconnected', () => {
        console.log('WebSocket连接断开')
      })

    // 监听任务错误
    webSocketService.on('task_error', (error) => {
      console.error('任务错误:', error)
      errorMessage.value = `任务错误: ${error.message}`
    })
    }

    // 订阅任务进度更新
    const subscribeTask = (taskId) => {
      webSocketService.subscribeTask(taskId)
    }

    // 取消任务
    const cancelTask = async (taskId) => {
      // 默认确认，直接执行取消
      errorMessage.value = ''
      successMessage.value = ''
      
      try {
        const response = await apiService.cancelTask(taskId)
        if (response.status === 200) {
          successMessage.value = '任务取消成功'
          // 不需要调用fetchTasks()，WebSocket会推送任务状态更新
        } else {
          errorMessage.value = '取消任务失败: ' + (response.message || '未知错误')
        }
      } catch (error) {
        console.error('取消任务错误:', error)
        errorMessage.value = '取消任务失败，请重试'
      }
    }

    // 清理已取消任务 - 确认状态
    const showClearConfirm = ref(false)
    
    const clearCancelledTasks = async () => {
      errorMessage.value = ''
      successMessage.value = ''
      
      // 显示确认提示而不是使用alert
      showClearConfirm.value = true
    }
    
    const confirmClearCancelledTasks = async () => {
      try {
        const response = await apiService.clearCancelledTasks()
        if (response.status === 200) {
          const result = response.data
          successMessage.value = `已成功清理 ${result.cleared_count} 个已取消的任务`
          
          // 重新获取任务列表以更新显示
          fetchTasks()
        } else {
          errorMessage.value = '清理已取消任务失败: ' + (response.message || '未知错误')
        }
      } catch (error) {
        console.error('清理已取消任务错误:', error)
        errorMessage.value = '清理已取消任务失败，请重试'
      } finally {
        showClearConfirm.value = false
      }
    }
    
    const cancelClearCancelledTasks = () => {
      showClearConfirm.value = false
      successMessage.value = '已取消清理操作'
    }

    // 清理已完成任务 - 确认状态
    const showClearCompletedConfirm = ref(false)
    
    const clearCompletedTasks = () => {
      errorMessage.value = ''
      successMessage.value = ''
      
      // 显示确认提示而不是直接执行
      showClearCompletedConfirm.value = true
    }
    
    const confirmClearCompletedTasks = () => {
      // 这里可以添加清理逻辑，目前只是显示提示
      successMessage.value = '已完成任务清理功能将在后续版本中实现'
      showClearCompletedConfirm.value = false
      // 不需要调用fetchTasks()，WebSocket会处理状态更新
    }
    
    const cancelClearCompletedTasks = () => {
      showClearCompletedConfirm.value = false
      successMessage.value = '已取消清理操作'
    }

    // 刷新任务列表（手动刷新，仅在需要时使用）
    const refreshTasks = () => {
      fetchTasks()
    }

    // 显示错误信息
    const showError = (errorMessage) => {
      errorMessage.value = `错误信息:\n${errorMessage}`
    }

    // 格式化时间
    const formatTime = (timestamp) => {
      if (!timestamp) return '未知'
      return new Date(timestamp * 1000).toLocaleString()
    }

    // 获取状态文本
    const getStatusText = (status) => {
      const statusMap = {
        'pending': '等待中',
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消'
      }
      return statusMap[status] || status
    }

    // 获取状态徽章类
    const getStatusBadgeClass = (status) => {
      const classMap = {
        'pending': 'bg-secondary',
        'running': 'bg-primary',
        'completed': 'bg-success',
        'failed': 'bg-danger',
        'cancelled': 'bg-warning'
      }
      return classMap[status] || 'bg-secondary'
    }

    // 获取任务类型文本
    const getTaskTypeText = (taskType) => {
        const typeMap = {
            'music_download': '单曲下载',
            'playlist_download': '歌单下载',
            'artist_download': '艺术家下载'
        }
        return typeMap[taskType] || taskType
    }

    // 获取任务显示名称，优先显示具体内容名称
    const getTaskDisplayName = (task) => {
        // 优先使用元数据中的内容名称
        if (task.metadata && task.metadata.content_name) {
            return task.metadata.content_name
        }
        // 如果没有内容名称，则显示任务类型
        return getTaskTypeText(task.task_type)
    }

    // 组件挂载时获取任务列表并启动WebSocket连接
    onMounted(() => {
        fetchTasks()
        handleWebSocketConnection()
    })

    // 组件卸载时断开WebSocket连接
    onUnmounted(() => {
      webSocketService.disconnect()
    })

    return {
      tasks,
      isLoading,
      showClearConfirm,
      showClearCompletedConfirm,
      fetchTasks,
      cancelTask,
      clearCancelledTasks,
      confirmClearCancelledTasks,
      cancelClearCancelledTasks,
      clearCompletedTasks,
      confirmClearCompletedTasks,
      cancelClearCompletedTasks,
      refreshTasks,
      showError,
      formatTime,
      getStatusText,
      getStatusBadgeClass,
      getTaskTypeText,
      getTaskDisplayName,
      subscribeTask,
      updateTaskProgress
    }
  }
}
</script>

<style scoped>
.task-item {
  transition: all 0.3s ease;
}

.task-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.progress {
  background-color: #e9ecef;
}

.badge {
  font-size: 0.7em;
}

.btn-sm {
  padding: 0.2rem 0.4rem;
  font-size: 0.8rem;
}
</style>

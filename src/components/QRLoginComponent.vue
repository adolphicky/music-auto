<template>
  <div class="qr-login-modal" v-if="showModal">
    <div class="modal-overlay" @click="closeModal"></div>
    <div class="modal-content">
      <div class="modal-header">
        <h3>重新登录</h3>
        <button class="close-btn" @click="closeModal">×</button>
      </div>
      
      <div class="modal-body">
        <div v-if="!qrCodeInfo" class="loading">
          <p>正在生成二维码...</p>
        </div>
        
        <div v-else-if="loginStatus === 'waiting'" class="qr-code-section">
          <p class="instruction">请使用网易云音乐APP扫描二维码</p>
          <div class="qr-code-container">
            <img :src="qrCodeInfo.qr_url" alt="登录二维码" class="qr-code">
          </div>
          <p class="expire-time">二维码有效期: {{ qrCodeInfo.expire_time }}秒</p>
        </div>
        
        <div v-else-if="loginStatus === 'success'" class="success-section">
          <div class="success-icon">✓</div>
          <p class="success-message">登录成功！</p>
          <p class="saving">正在保存Cookie...</p>
        </div>
        
        <div v-else-if="loginStatus === 'expired'" class="expired-section">
          <p class="expired-message">二维码已过期</p>
          <button class="retry-btn" @click="generateQRCode">重新生成二维码</button>
        </div>
        
        <div v-else-if="loginStatus === 'error'" class="error-section">
          <p class="error-message">登录失败，请重试</p>
          <button class="retry-btn" @click="generateQRCode">重试</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import apiService from '../services/apiService'

export default {
  name: 'QRLoginComponent',
  setup() {
    const showModal = ref(false)
    const qrCodeInfo = ref(null)
    const loginStatus = ref('waiting') // waiting, success, expired, error
    const checkInterval = ref(null)

    // 生成二维码
    const generateQRCode = async () => {
      try {
        loginStatus.value = 'waiting'
        qrCodeInfo.value = null
        
        // 直接调用二维码API，不需要先检查健康状态
        const qrResponse = await fetch('/api/auth/qr-code')
        const qrData = await qrResponse.json()
        
        if (qrData.success) {
          qrCodeInfo.value = qrData.data
          startCheckingLoginStatus()
        } else {
          console.error('二维码生成失败:', qrData.message)
          loginStatus.value = 'error'
        }
      } catch (error) {
        console.error('生成二维码失败:', error)
        loginStatus.value = 'error'
      }
    }

    // 开始检查登录状态
    const startCheckingLoginStatus = () => {
      if (checkInterval.value) {
        clearInterval(checkInterval.value)
      }
      
      checkInterval.value = setInterval(async () => {
        if (!qrCodeInfo.value) return
        
        try {
          const response = await fetch('/api/auth/check-login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ qr_key: qrCodeInfo.value.qr_key })
          })
          
          const data = await response.json()
          
          if (data.success) {
            const status = data.data.status
            
            if (status === 'success') {
              // 登录成功，保存cookie
              const saveSuccess = await saveCookie(data.data.cookie)
              if (saveSuccess) {
                loginStatus.value = 'success'
                clearInterval(checkInterval.value)
                
                // 延迟关闭模态框并刷新页面，让新的cookie生效
                setTimeout(() => {
                  showModal.value = false
                  if (typeof window !== 'undefined') {
                    if (window.showGlobalMessage) {
                      window.showGlobalMessage('重新登录成功', 'success')
                    }
                    // 刷新页面使新的cookie生效
                    window.location.reload()
                  }
                }, 2000)
              } else {
                // 保存cookie失败
                loginStatus.value = 'error'
                console.error('保存Cookie失败')
              }
              
            } else if (status === 'expired') {
              loginStatus.value = 'expired'
              clearInterval(checkInterval.value)
            }
          }
        } catch (error) {
          console.error('检查登录状态失败:', error)
        }
      }, 2000) // 每2秒检查一次
    }

    // 保存cookie到后端
    const saveCookie = async (cookie) => {
      try {
        const response = await fetch('/api/auth/save-cookie', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ cookie })
        })
        
        const data = await response.json()
        return data.success
      } catch (error) {
        console.error('保存Cookie失败:', error)
        return false
      }
    }

    // 打开模态框
    const openModal = () => {
      showModal.value = true
      generateQRCode()
    }

    // 关闭模态框
    const closeModal = () => {
      showModal.value = false
      if (checkInterval.value) {
        clearInterval(checkInterval.value)
        checkInterval.value = null
      }
      qrCodeInfo.value = null
      loginStatus.value = 'waiting'
    }

    // 将openModal函数挂载到window对象
    onMounted(() => {
      if (typeof window !== 'undefined') {
        window.triggerReLogin = openModal
      }
    })

    // 清理定时器
    onUnmounted(() => {
      if (checkInterval.value) {
        clearInterval(checkInterval.value)
      }
    })

    return {
      showModal,
      qrCodeInfo,
      loginStatus,
      generateQRCode,
      openModal,
      closeModal
    }
  }
}
</script>

<style scoped>
.qr-login-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
}

.modal-content {
  position: relative;
  background: white;
  border-radius: 8px;
  padding: 0;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  z-index: 1001;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
  text-align: center;
}

.loading, .qr-code-section, .success-section, .expired-section, .error-section {
  padding: 20px 0;
}

.instruction {
  margin-bottom: 20px;
  color: #666;
}

.qr-code-container {
  margin: 20px 0;
}

.qr-code {
  max-width: 200px;
  height: auto;
  border: 1px solid #eee;
  border-radius: 4px;
}

.expire-time {
  color: #999;
  font-size: 14px;
}

.success-icon {
  font-size: 48px;
  color: #28a745;
  margin-bottom: 10px;
}

.success-message {
  color: #28a745;
  font-weight: bold;
  margin-bottom: 10px;
}

.saving {
  color: #666;
}

.expired-message, .error-message {
  color: #dc3545;
  margin-bottom: 20px;
}

.retry-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}

.retry-btn:hover {
  background: #0056b3;
}
</style>

<template>
  <div class="chat-container">
    <div class="chat-header">
      <h2>💬 AI 对话助手</h2>
      <button @click="clearHistory" class="clear-btn">清除历史</button>
    </div>
    
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">🤖</div>
        <p>开始与AI助手对话吧！</p>
        <p class="hint">您可以询问任何问题，我会尽力为您解答。</p>
      </div>
      
      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
        <div class="message-avatar">
          {{ msg.role === 'user' ? '👤' : '🤖' }}
        </div>
        <div class="message-content">
          <div class="message-text">{{ msg.content }}</div>
          <div class="message-time">{{ msg.time }}</div>
        </div>
      </div>
      
      <div v-if="isLoading" class="message assistant loading">
        <div class="message-avatar">🤖</div>
        <div class="message-content">
          <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="chat-input">
      <div class="input-wrapper">
        <textarea 
          v-model="inputMessage" 
          @keydown.enter.prevent="sendMessage"
          placeholder="输入您的问题..."
          rows="1"
          ref="inputArea"
          @input="autoResize"
        ></textarea>
        <button 
          @click="sendMessage" 
          :disabled="!inputMessage.trim() || isLoading"
          class="send-btn"
        >
          <span v-if="!isLoading">发送</span>
          <span v-else>...</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const inputArea = ref(null)

const API_URL = 'http://localhost:5000/api/chat'
const CLEAR_API_URL = 'http://localhost:5000/api/chat/clear'

const getToken = () => {
  return localStorage.getItem('token')
}

const formatTime = () => {
  const now = new Date()
  return now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const autoResize = () => {
  if (inputArea.value) {
    inputArea.value.style.height = 'auto'
    inputArea.value.style.height = Math.min(inputArea.value.scrollHeight, 120) + 'px'
  }
}

const sendMessage = async () => {
  const message = inputMessage.value.trim()
  if (!message || isLoading.value) return

  const token = getToken()
  if (!token) {
    alert('请先登录')
    return
  }

  messages.value.push({
    role: 'user',
    content: message,
    time: formatTime()
  })

  inputMessage.value = ''
  if (inputArea.value) {
    inputArea.value.style.height = 'auto'
  }

  isLoading.value = true
  scrollToBottom()

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ message })
    })

    if (!response.ok) {
      throw new Error('网络请求失败')
    }

    const data = await response.json()

    messages.value.push({
      role: 'assistant',
      content: data.response,
      time: formatTime()
    })
  } catch (error) {
    console.error('发送消息失败:', error)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，发送消息时出现错误。请稍后重试。',
      time: formatTime()
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const clearHistory = async () => {
  const token = getToken()
  if (!token) {
    alert('请先登录')
    return
  }

  try {
    const response = await fetch(CLEAR_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error('清除历史失败')
    }

    messages.value = []
    alert('对话历史已清除')
  } catch (error) {
    console.error('清除历史失败:', error)
    alert('清除历史失败，请稍后重试')
  }
}

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom: 1px solid #e5e7eb;
}

.chat-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.clear-btn {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.clear-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f9fafb;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6b7280;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 8px 0;
  font-size: 16px;
}

.empty-state .hint {
  font-size: 14px;
  color: #9ca3af;
}

.message {
  display: flex;
  margin-bottom: 20px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  background: #e5e7eb;
}

.message.user .message-avatar {
  background: #667eea;
  color: white;
  margin-left: 12px;
}

.message.assistant .message-avatar {
  background: #764ba2;
  color: white;
  margin-right: 12px;
}

.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.5;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.message.user .message-text {
  background: #667eea;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-text {
  background: white;
  color: #1f2937;
  border: 1px solid #e5e7eb;
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.message.user .message-time {
  text-align: right;
}

.message.loading .message-text {
  background: #f3f4f6;
  color: #9ca3af;
}

.loading-dots {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: white;
  border-radius: 12px;
  border-bottom-left-radius: 4px;
  border: 1px solid #e5e7eb;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.chat-input {
  padding: 20px 24px;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

textarea {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 15px;
  font-family: inherit;
  resize: none;
  outline: none;
  transition: all 0.3s ease;
  min-height: 48px;
  max-height: 120px;
}

textarea:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

textarea::placeholder {
  color: #9ca3af;
}

.send-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s ease;
  min-width: 80px;
  height: 48px;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}
</style>

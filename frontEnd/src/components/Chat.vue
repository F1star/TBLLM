<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="header-left">
        <div class="header-icon">🤖</div>
        <h2>AI 对话助手</h2>
      </div>
      <button @click="clearHistory" class="clear-btn">
        <span class="btn-icon">🗑️</span>
        <span>清除历史</span>
      </button>
    </div>
    
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">🤖</div>
        <p class="empty-title">开始与AI助手对话吧！</p>
        <p class="empty-hint">您可以询问任何问题，我会尽力为您解答。</p>
        <div class="quick-actions">
          <button @click="quickAsk('你好')" class="quick-btn">👋 你好</button>
          <button @click="quickAsk('介绍一下你自己')" class="quick-btn">🎯 介绍自己</button>
          <button @click="quickAsk('你能帮我做什么？')" class="quick-btn">💡 功能介绍</button>
        </div>
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
    inputArea.value.style.height = Math.min(inputArea.value.value.split('\n').length * 24 + 24, 150) + 'px'
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

const quickAsk = (question) => {
  inputMessage.value = question
  sendMessage()
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
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  font-size: 32px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

.chat-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.clear-btn {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 8px;
  backdrop-filter: blur(10px);
}

.clear-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.3);
}

.btn-icon {
  font-size: 16px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #64748b;
  text-align: center;
  padding: 40px 20px;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 24px;
  filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.1));
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.empty-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #1e293b;
  letter-spacing: -0.5px;
}

.empty-hint {
  font-size: 16px;
  color: #64748b;
  margin-bottom: 32px;
  font-weight: 500;
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.quick-btn {
  padding: 12px 24px;
  background: white;
  color: #667eea;
  border: 2px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.quick-btn:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  border-color: transparent;
}

.message {
  display: flex;
  margin-bottom: 24px;
  animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
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
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  margin-left: 16px;
}

.message.assistant .message-avatar {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  margin-right: 16px;
}

.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
}

.message-text {
  padding: 16px 20px;
  border-radius: 16px;
  font-size: 16px;
  line-height: 1.6;
  word-wrap: break-word;
  white-space: pre-wrap;
  font-weight: 500;
;
}

.message.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.message.assistant .message-text {
  background: white;
  color: #1e293b;
  border: 2px solid rgba(0, 0, 0, 0.05);
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.message-time {
  font-size: 13px;
  color: #94a3b8;
  margin-top: 8px;
  font-weight: 500;
}

.message.user .message-time {
  text-align: right;
}

.message.loading .message-text {
  background: #f8fafc;
  color: #94a3b8;
  border: 2px dashed rgba(0, 0, 0, 0.1);
}

.loading-dots {
  display: flex;
  gap: 6px;
  padding: 16px 20px;
  background: white;
  border-radius: 16px;
  border-bottom-left-radius: 4px;
  border: 2px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.loading-dots span {
  width: 10px;
  height: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
  padding: 24px 32px;
  background: white;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05);
}

.input-wrapper {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  max-width: 100%;
}

textarea {
  flex: 1;
  padding: 16px 20px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: 16px;
  font-size: 16px;
  font-family: inherit;
  resize: none;
  outline: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 56px;
  max-height: 150px;
  background: #f8fafc;
  color: #1e293b;
  font-weight: 500;
  line-height: 1.5;
}

textarea:focus {
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

textarea::placeholder {
  color: #94a3b8;
}

.send-btn {
  padding: 16px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 700;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 100px;
  height: 56px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  letter-spacing: 0.5px;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.send-btn:active:not(:disabled) {
  transform: translateY(0);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #764ba2 0%, #667eea 100%);
}

@media (max-width: 768px) {
  .chat-header {
    padding: 20px 24px;
  }
  
  .chat-header h2 {
    font-size: 20px;
  }
  
  .chat-messages {
    padding: 24px 20px;
  }
  
  .message-content {
    max-width: 85%;
  }
  
  .chat-input {
    padding: 20px 24px;
  }
  
  .quick-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .quick-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .chat-header {
    padding: 16px 20px;
  }
  
  .chat-header h2 {
    font-size: 18px;
  }
  
  .header-icon {
    font-size: 28px;
  }
  
  .clear-btn {
    padding: 8px 16px;
    font-size: 14px;
  }
  
  .chat-messages {
    padding: 20px 16px;
  }
  
  .message-avatar {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }
  
  .message-text {
    padding: 14px 18px;
    font-size: 15px;
  }
  
  .chat-input {
    padding: 16px 20px;
  }
  
  .input-wrapper {
    gap: 12px;
  }
  
  textarea {
    padding: 14px 18px;
    font-size: 15px;
    min-height: 48px;
  }
  
  .send-btn {
    padding: 14px 24px;
    font-size: 15px;
    min-width: 80px;
    height: 48px;
  }
}
</style>

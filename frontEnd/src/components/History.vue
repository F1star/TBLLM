<template>
  <div class="history-container">
    <div class="history-header">
      <div class="header-left">
        <h2>📋 对话历史记录</h2>
        <div v-if="currentSession" class="session-info">
          <span class="session-name">{{ currentSession.name }}</span>
          <button @click="showSessionSelector = !showSessionSelector" class="session-select-btn">
            <span>▼</span>
          </button>
        </div>
        <div v-else class="session-info">
          <span class="no-session">未选择会话</span>
          <button @click="showSessionSelector = !showSessionSelector" class="session-select-btn">
            <span>选择会话</span>
          </button>
        </div>
      </div>
      <div class="header-actions">
        <button @click="loadHistory" class="refresh-btn">
          <span>🔄</span>
          <span>刷新</span>
        </button>
        <button @click="clearHistory" class="clear-btn">
          <span>🗑️</span>
          <span>清空历史</span>
        </button>
      </div>
    </div>

    <!-- 会话选择器下拉菜单 -->
    <div v-if="showSessionSelector" class="session-selector-overlay" @click="showSessionSelector = false"></div>
    <div v-if="showSessionSelector" class="session-selector">
      <div class="selector-header">
        <h3>选择会话</h3>
        <button @click="showSessionSelector = false" class="close-selector">✕</button>
      </div>
      <div v-if="sessionsLoading" class="loading-sessions">加载中...</div>
      <div v-else-if="sessions.length === 0" class="no-sessions">
        <p>暂无会话</p>
        <button @click="createNewSession" class="create-session-btn">创建新会话</button>
      </div>
      <div v-else class="sessions-list">
        <div
          v-for="session in sessions"
          :key="session.id"
          :class="['session-item', { active: currentSession && currentSession.id === session.id }]"
          @click="selectSession(session)"
        >
          <div class="session-item-name">{{ session.name }}</div>
          <div class="session-item-meta">{{ session.message_count }} 条消息 · {{ formatSessionDate(session.updated_at) }}</div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="history.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <p class="empty-title">暂无对话记录</p>
      <p class="empty-hint">开始与AI对话，记录将显示在这里</p>
    </div>

    <div v-else class="history-list">
      <div v-for="(item, index) in groupedHistory" :key="item.date" class="history-group">
        <div class="group-header">
          <span class="group-date">{{ item.date }}</span>
          <span class="group-count">{{ item.messages.length }} 条记录</span>
        </div>
        
        <div v-for="msg in item.messages" :key="msg.id" class="history-item" @click="viewMessage(msg)">
          <div class="message-avatar">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-role">{{ msg.role === 'user' ? '用户' : 'AI助手' }}</span>
              <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
            </div>
            <div class="message-text">{{ truncateText(msg.content, 100) }}</div>
          </div>
          <div class="message-actions">
            <button @click.stop="evaluateMessage(msg)" class="evaluate-btn" :disabled="msg.evaluating">
              <span v-if="!msg.evaluating">⭐</span>
              <span v-else>⏳</span>
              <span>{{ msg.evaluating ? '评估中...' : '评估' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedMessage" class="message-modal" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ selectedMessage.role === 'user' ? '用户消息' : 'AI回复' }}</h3>
          <button @click="closeModal" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="full-message">{{ selectedMessage.content }}</div>
          <div v-if="selectedMessage.evaluation" class="evaluation-section">
            <h4>评估结果</h4>
            <div class="evaluation-grid">
              <div class="evaluation-item">
                <span class="evaluation-label">逻辑思维</span>
                <span class="evaluation-score" :class="getScoreClass(selectedMessage.evaluation.logic_score)">
                  {{ selectedMessage.evaluation.logic_score }}
                </span>
              </div>
              <div class="evaluation-item">
                <span class="evaluation-label">创造力</span>
                <span class="evaluation-score" :class="getScoreClass(selectedMessage.evaluation.creativity_score)">
                  {{ selectedMessage.evaluation.creativity_score }}
                </span>
              </div>
              <div class="evaluation-item">
                <span class="evaluation-label">表达能力</span>
                <span class="evaluation-score" :class="getScoreClass(selectedMessage.evaluation.expression_score)">
                  {{ selectedMessage.evaluation.expression_score }}
                </span>
              </div>
              <div class="evaluation-item">
                <span class="evaluation-label">知识广度</span>
                <span class="evaluation-score" :class="getScoreClass(selectedMessage.evaluation.knowledge_score)">
                  {{ selectedMessage.evaluation.knowledge_score }}
                </span>
              </div>
            </div>
            <div class="overall-score">
              <span class="overall-label">综合评分</span>
              <span class="overall-value" :class="getScoreClass(selectedMessage.evaluation.overall_score)">
                {{ selectedMessage.evaluation.overall_score }}
              </span>
            </div>
            <div v-if="selectedMessage.evaluation.feedback" class="feedback-section">
              <h4>反馈意见</h4>
              <p>{{ selectedMessage.evaluation.feedback }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const history = ref([])
const loading = ref(false)
const selectedMessage = ref(null)

// 会话相关状态
const currentSession = ref(null)
const showSessionSelector = ref(false)
const sessions = ref([])
const sessionsLoading = ref(false)

const API_URL = 'http://localhost:5000/api/chat/history'
const CLEAR_API_URL = 'http://localhost:5000/api/chat/clear'
const EVALUATE_API_URL = 'http://localhost:5000/api/evaluate'
const SESSIONS_API_URL = 'http://localhost:5000/api/sessions'

const getToken = () => {
  return localStorage.getItem('token')
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const formatDate = (timestamp) => {
  const date = new Date(timestamp)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  if (date.toDateString() === today.toDateString()) {
    return '今天'
  } else if (date.toDateString() === yesterday.toDateString()) {
    return '昨天'
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })
  }
}

const formatSessionDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 加载会话列表
const loadSessions = async () => {
  const token = getToken()
  if (!token) return false

  sessionsLoading.value = true
  try {
    const response = await fetch(SESSIONS_API_URL, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (response.ok) {
      const data = await response.json()
      sessions.value = data
      return true
    }
    return false
  } catch (error) {
    console.error('加载会话失败:', error)
    return false
  } finally {
    sessionsLoading.value = false
  }
}

// 选择会话
const selectSession = async (session) => {
  currentSession.value = session
  showSessionSelector.value = false
  // 保存到localStorage
  localStorage.setItem('current_session_id', session.id)
  localStorage.setItem('current_session_name', session.name)
  // 加载该会话的消息
  await loadHistory()
}

// 创建新会话
const createNewSession = async () => {
  const token = getToken()
  if (!token) {
    alert('请先登录')
    return
  }

  const sessionName = prompt('请输入会话名称（可选）:') || ''

  try {
    const response = await fetch(SESSIONS_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ name: sessionName })
    })

    if (response.ok) {
      const session = await response.json()
      sessions.value.unshift(session)
      await selectSession(session)
      alert('会话创建成功！')
    } else {
      const error = await response.json()
      alert('创建失败: ' + (error.error || '未知错误'))
    }
  } catch (error) {
    console.error('创建会话失败:', error)
    alert('创建失败，请稍后重试')
  }
}

const truncateText = (text, maxLength) => {
  if (!text) {
    return ''
  }
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

const getScoreClass = (score) => {
  if (score >= 90) {
    return 'excellent'
  } else if (score >= 80) {
    return 'good'
  } else if (score >= 60) {
    return 'average'
  } else {
    return 'poor'
  }
}

const groupedHistory = computed(() => {
  const groups = {}
  history.value.forEach((item) => {
    const date = formatDate(item.timestamp)
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(item)
  })
  
  return Object.keys(groups).map((date) => ({
    date,
    messages: groups[date] || []
  }))
})

const loadHistory = async () => {
  const token = getToken()
  if (!token) {
    alert('请先登录')
    return
  }

  loading.value = true
  try {
    let url = API_URL
    if (currentSession.value) {
      url += `?session_id=${currentSession.value.id}`
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error('获取历史记录失败')
    }

    const data = await response.json()
    history.value = data
  } catch (error) {
    console.error('获取历史记录失败:', error)
    alert('获取历史记录失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const clearHistory = async () => {
  // 确认清除
  const sessionName = currentSession.value ? currentSession.value.name : '所有'
  const confirmMessage = currentSession.value
    ? `确定要清空会话 "${sessionName}" 的历史记录吗？`
    : '确定要清空所有历史记录吗？'

  if (!confirm(confirmMessage)) {
    return
  }

  const token = getToken()
  if (!token) {
    alert('请先登录')
    return
  }

  try {
    const requestBody = {}
    if (currentSession.value) {
      requestBody.session_id = currentSession.value.id
    }

    const response = await fetch(CLEAR_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      throw new Error('清空历史失败')
    }

    history.value = []
    alert(currentSession.value ? '会话历史已清空' : '所有历史记录已清空')
  } catch (error) {
    console.error('清空历史失败:', error)
    alert('清空历史失败，请稍后重试')
  }
}

const viewMessage = (msg) => {
  selectedMessage.value = msg
}

const closeModal = () => {
  selectedMessage.value = null
}

const evaluateMessage = async (msg) => {
  const token = getToken()
  if (!token) {
    alert('请先登录')
    return
  }

  msg.evaluating = true

  try {
    const response = await fetch(EVALUATE_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ chat_id: msg.id })
    })

    if (!response.ok) {
      throw new Error('评估失败')
    }

    const data = await response.json()
    msg.evaluation = data
    alert('评估完成！')
  } catch (error) {
    console.error('评估失败:', error)
    alert('评分失败，请稍后重试')
  } finally {
    msg.evaluating = false
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.history-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  background: white;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.history-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  letter-spacing: -0.5px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.refresh-btn, .clear-btn {
  padding: 10px 20px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 6px;
  background: white;
}

.refresh-btn:hover, .clear-btn:hover {
  background: #f8fafc;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.clear-btn {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.clear-btn:hover {
  background: rgba(239, 68, 68, 0.2);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #64748b;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(102, 126, 234, 0.2);
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #64748b;
  text-align: center;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 24px;
  filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.1));
}

.empty-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #1e293b;
}

.empty-hint {
  font-size: 16px;
  color: #64748b;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

.history-group {
  margin-bottom: 32px;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.group-date {
  font-size: 16px;
  font-weight: 700;
}

.group-count {
  font-size: 14px;
  font-weight: 600;
  opacity: 0.9;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.history-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.message-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-role {
  font-size: 14px;
  font-weight: 700;
  color: #667eea;
}

.message-time {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
}

.message-text {
  font-size: 15px;
  color: #334155;
  line-height: 1.6;
  font-weight: 500;
}

.message-actions {
  flex-shrink: 0;
}

.evaluate-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 6px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.evaluate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.evaluate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.message-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 20px;
  max-width: 700px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.close-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: #f8fafc;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  transition: all 0.3s;
}

.close-btn:hover {
  background: #e2e8f0;
  transform: rotate(90deg);
}

.modal-body {
  padding: 28px;
}

.full-message {
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  font-size: 16px;
  line-height: 1.8;
  color: #1e293b;
  margin-bottom: 24px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.evaluation-section {
  margin-top: 24px;
}

.evaluation-section h4 {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 16px;
}

.evaluation-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.evaluation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 2px solid rgba(0, 0, 0, 0.05);
}

.evaluation-label {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
}

.evaluation-score {
  font-size: 24px;
  font-weight: 800;
  padding: 8px 16px;
  border-radius: 8px;
}

.evaluation-score.excellent {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.evaluation-score.good {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.evaluation-score.average {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.evaluation-score.poor {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.overall-score {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  margin-bottom: 24px;
  color: white;
}

.overall-label {
  font-size: 18px;
  font-weight: 700;
}

.overall-value {
  font-size: 32px;
  font-weight: 800;
  padding: 8px 20px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
}

.feedback-section h4 {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 12px;
}

.feedback-section p {
  font-size: 15px;
  line-height: 1.8;
  color: #64748b;
  background: #f8fafc;
  padding: 16px;
  border-radius: 12px;
  border-left: 4px solid #667eea;
}

.history-list::-webkit-scrollbar {
  width: 8px;
}

.history-list::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.history-list::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
}

@media (max-width: 768px) {
  .history-header {
    padding: 20px 24px;
  }
  
  .history-header h2 {
    font-size: 20px;
  }
  
  .history-list {
    padding: 20px 24px;
  }
  
  .evaluation-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    max-height: 95vh;
  }
}

@media (max-width: 480px) {
  .history-header {
    padding: 16px 20px;
    flex-direction: column;
    gap: 16px;
  }
  
  .history-header h2 {
    font-size: 18px;
  }
  
  .history-list {
    padding: 16px 20px;
  }
  
  .history-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .message-avatar {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }
  
  .message-content {
    width: 100%;
  }
  
  .message-actions {
    width: 100%;
    margin-top: 12px;
  }
  
  .evaluate-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>

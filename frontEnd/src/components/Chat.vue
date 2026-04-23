<template>
  <div class="chat-container">
    <!-- Header -->
    <div class="chat-header">
      <div class="header-left">
        <div class="header-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <div class="header-info">
          <h2>AI 对话助手</h2>
          <div class="session-info">
            <span v-if="currentSession" class="session-name">{{ currentSession.name }}</span>
            <span v-else class="no-session">未选择会话</span>
            <button @click="showSessionSelector = !showSessionSelector" class="session-select-btn">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
            </button>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <button @click="createNewSession" class="action-btn" title="新建会话">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        </button>
        <button v-if="currentSession" @click="evaluateSession" class="action-btn" title="评估会话">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
        </button>
        <button @click="clearHistory" class="action-btn danger" title="清除历史">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
        </button>
      </div>
    </div>

    <!-- Session Selector -->
    <div v-if="showSessionSelector" class="selector-overlay" @click="showSessionSelector = false"></div>
    <div v-if="showSessionSelector" class="session-selector">
      <div class="selector-header">
        <h3>选择会话</h3>
        <button @click="showSessionSelector = false" class="close-btn">&times;</button>
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
          <div class="session-item-meta">{{ session.message_count }} 条消息</div>
        </div>
      </div>
    </div>

    <!-- Messages -->
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" opacity="0.2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <p class="empty-title">开始与AI助手对话吧！</p>
        <p class="empty-hint">您可以询问任何问题，我会尽力为您解答</p>
        <div class="quick-actions">
          <button @click="quickAsk('你好')" class="quick-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
            你好</button>
          <button @click="quickAsk('介绍一下你自己')" class="quick-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1-8.313-12.454z"/></svg>
            介绍自己</button>
          <button @click="quickAsk('你能帮我做什么？')" class="quick-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
            功能介绍</button>
        </div>
      </div>

      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
        <div class="message-avatar">
          <svg v-if="msg.role === 'assistant'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1-8.313-12.454z"/></svg>
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        </div>
        <div class="message-content">
          <div class="message-text">{{ msg.content }}</div>
          <div class="message-time">{{ msg.time }}</div>
        </div>
      </div>

      <div v-if="isLoading" class="message assistant">
        <div class="message-avatar">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1-8.313-12.454z"/></svg>
        </div>
        <div class="message-content">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input -->
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
        <button @click="sendMessage" :disabled="!inputMessage.trim() || isLoading" class="send-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
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

const currentSession = ref(null)
const showSessionSelector = ref(false)
const sessions = ref([])
const sessionsLoading = ref(false)

const API_URL = 'http://localhost:5000/api/chat'
const CLEAR_API_URL = 'http://localhost:5000/api/chat/clear'
const EVALUATE_API_URL = 'http://localhost:5000/api/evaluate'

const getToken = () => localStorage.getItem('token')

const formatTime = (ts) => {
  const d = ts ? new Date(ts) : new Date()
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
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
  if (!token) { alert('请先登录'); return }

  messages.value.push({ role: 'user', content: message, time: formatTime() })
  inputMessage.value = ''
  if (inputArea.value) inputArea.value.style.height = 'auto'
  isLoading.value = true
  scrollToBottom()

  try {
    const body = { message }
    if (currentSession.value) body.session_id = currentSession.value.id
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(body)
    })
    if (!res.ok) throw new Error('请求失败')
    const data = await res.json()
    messages.value.push({ role: 'assistant', content: data.response, time: formatTime() })
  } catch (e) {
    console.error('发送失败:', e)
    messages.value.push({ role: 'assistant', content: '发送消息时出现错误，请稍后重试。', time: formatTime() })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const quickAsk = (q) => { inputMessage.value = q; sendMessage() }

const clearHistory = async () => {
  const name = currentSession.value ? currentSession.value.name : '所有'
  if (!confirm(`确定要清空会话 "${name}" 的历史记录吗？`)) return
  const token = getToken()
  if (!token) return
  try {
    const body = {}
    if (currentSession.value) body.session_id = currentSession.value.id
    const res = await fetch(CLEAR_API_URL, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    if (!res.ok) throw new Error('清除失败')
    messages.value = []
    alert('历史记录已清除')
  } catch (e) { console.error(e); alert('清除失败') }
}

const evaluateSession = async () => {
  if (!currentSession.value) { alert('请先选择会话'); return }
  if (!confirm(`确定要评估会话 "${currentSession.value.name}" 吗？`)) return
  const token = getToken()
  try {
    const res = await fetch(EVALUATE_API_URL, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: currentSession.value.id })
    })
    if (!res.ok) throw new Error('评估失败')
    const r = await res.json()
    alert(`评估完成！\n逻辑思维: ${r.logic_score}\n创造力: ${r.creativity_score}\n表达能力: ${r.expression_score}\n知识掌握: ${r.knowledge_score}\n综合得分: ${r.overall_score}\n\n反馈: ${r.feedback}`)
  } catch (e) { console.error(e); alert('评估失败: ' + e.message) }
}

const loadSessions = async () => {
  const token = getToken()
  if (!token) return false
  sessionsLoading.value = true
  try {
    const res = await fetch('http://localhost:5000/api/sessions', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) { sessions.value = await res.json(); return true }
    return false
  } catch (e) { console.error(e); return false }
  finally { sessionsLoading.value = false }
}

const selectSession = async (session) => {
  currentSession.value = session
  showSessionSelector.value = false
  localStorage.setItem('current_session_id', session.id)
  localStorage.setItem('current_session_name', session.name)
  await loadSessionMessages()
}

const createNewSession = async () => {
  const token = getToken()
  if (!token) { alert('请先登录'); return }
  const name = prompt('请输入会话名称（可选）:') || ''
  try {
    const res = await fetch('http://localhost:5000/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ name })
    })
    if (res.ok) {
      const session = await res.json()
      sessions.value.unshift(session)
      await selectSession(session)
    } else {
      const e = await res.json()
      alert('创建失败: ' + (e.error || '未知错误'))
    }
  } catch (e) { console.error(e); alert('创建失败') }
}

const loadSessionMessages = async () => {
  if (!currentSession.value) { messages.value = []; return }
  const token = getToken()
  if (!token) return
  try {
    const res = await fetch(`http://localhost:5000/api/chat/history?session_id=${currentSession.value.id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      const data = await res.json()
      messages.value = data.map(msg => ({ ...msg, time: formatTime(msg.timestamp) }))
      scrollToBottom()
    }
  } catch (e) { console.error(e) }
}

const initialize = async () => {
  await loadSessions()
  const savedId = localStorage.getItem('current_session_id')
  if (savedId && sessions.value.length > 0) {
    const found = sessions.value.find(s => s.id === parseInt(savedId))
    if (found) {
      currentSession.value = found
      await loadSessionMessages()
    }
  }
  scrollToBottom()
}

onMounted(() => {
  initialize()
  window.addEventListener('storage', (e) => {
    if (e.key === 'current_session_id' || e.key === 'current_session_name') initialize()
  })
  window.addEventListener('session-changed', () => initialize())
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgba(7,11,20,0.6);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  overflow: hidden;
  position: relative;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(13,20,33,0.6);
  border-bottom: 1px solid rgba(255,255,255,0.06);
  backdrop-filter: blur(12px);
}

.header-left { display: flex; align-items: center; gap: 12px; }

.header-icon {
  width: 40px;
  height: 40px;
  background: rgba(0,229,255,0.08);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-cyan, #00e5ff);
}

.header-info h2 {
  font-family: 'Orbitron', sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: #e8eaed;
  letter-spacing: 1px;
  margin: 0;
}

.session-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

.session-name, .no-session {
  font-size: 11px;
  color: #5a6275;
}

.session-select-btn {
  background: none;
  border: none;
  color: #5a6275;
  cursor: pointer;
  padding: 2px;
  display: flex;
  transition: color 0.2s;
}

.session-select-btn:hover { color: #00e5ff; }

.header-actions { display: flex; gap: 8px; }

.action-btn {
  width: 36px;
  height: 36px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  color: #5a6275;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.action-btn:hover {
  background: rgba(0,229,255,0.08);
  color: #00e5ff;
  border-color: rgba(0,229,255,0.2);
}

.action-btn.danger:hover {
  background: rgba(255,23,68,0.08);
  color: #ff1744;
  border-color: rgba(255,23,68,0.2);
}

/* Session Selector */
.selector-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200;
}
.session-selector {
  position: absolute; top: 76px; left: 24px; width: 300px;
  background: rgba(13,20,33,0.95);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(0,229,255,0.12);
  border-radius: 12px;
  z-index: 201;
  max-height: 400px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.selector-header h3 {
  font-family: 'Orbitron', sans-serif;
  font-size: 12px;
  font-weight: 600;
  color: #e8eaed;
  letter-spacing: 1px;
}

.close-btn {
  background: none; border: none; color: #5a6275;
  font-size: 20px; cursor: pointer;
}

.loading-sessions, .no-sessions { padding: 24px; text-align: center; color: #5a6275; font-size: 13px; }

.create-session-btn {
  margin-top: 12px;
  padding: 8px 20px;
  background: rgba(0,229,255,0.1);
  color: #00e5ff;
  border: 1px solid rgba(0,229,255,0.2);
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  font-family: 'JetBrains Mono', monospace;
}

.sessions-list { overflow-y: auto; padding: 8px; }

.session-item {
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.session-item:hover { background: rgba(255,255,255,0.04); }
.session-item.active { background: rgba(0,229,255,0.06); border: 1px solid rgba(0,229,255,0.12); }

.session-item-name { font-size: 13px; color: #e8eaed; font-weight: 500; margin-bottom: 4px; }
.session-item-meta { font-size: 11px; color: #5a6275; }

/* Messages */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: 40px 20px;
}

.empty-icon { color: #5a6275; margin-bottom: 24px; }

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #e8eaed;
  margin-bottom: 8px;
}

.empty-hint { font-size: 13px; color: #5a6275; margin-bottom: 28px; }

.quick-actions { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }

.quick-btn {
  padding: 10px 20px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  color: #8892a4;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.quick-btn:hover {
  background: rgba(0,229,255,0.08);
  border-color: rgba(0,229,255,0.2);
  color: #00e5ff;
}

.message {
  display: flex;
  gap: 12px;
  animation: msgIn 0.3s ease;
}

@keyframes msgIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user { flex-direction: row-reverse; }

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: linear-gradient(135deg, rgba(0,229,255,0.15), rgba(124,77,255,0.15));
  color: #00e5ff;
}

.message.assistant .message-avatar {
  background: linear-gradient(135deg, rgba(124,77,255,0.15), rgba(0,229,255,0.15));
  color: #7c4dff;
}

.message-content { max-width: 70%; display: flex; flex-direction: column; gap: 4px; }

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.message.user .message-text {
  background: linear-gradient(135deg, rgba(0,229,255,0.1), rgba(124,77,255,0.1));
  border: 1px solid rgba(0,229,255,0.15);
  color: #e8eaed;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-text {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  color: #e8eaed;
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 11px;
  color: #5a6275;
  padding: 0 4px;
}

.message.user .message-time { text-align: right; }

.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 12px 16px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  border-bottom-left-radius: 4px;
}

.typing-indicator span {
  width: 8px; height: 8px;
  background: linear-gradient(135deg, #00e5ff, #7c4dff);
  border-radius: 50%;
  animation: typingBounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* Input */
.chat-input {
  padding: 16px 24px;
  background: rgba(13,20,33,0.6);
  border-top: 1px solid rgba(255,255,255,0.06);
  backdrop-filter: blur(12px);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

textarea {
  flex: 1;
  padding: 12px 16px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  color: #e8eaed;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  resize: none;
  outline: none;
  transition: all 0.3s;
  min-height: 44px;
  max-height: 150px;
  line-height: 1.5;
}

textarea:focus {
  border-color: rgba(0,229,255,0.3);
  box-shadow: 0 0 20px rgba(0,229,255,0.04);
}

textarea::placeholder { color: #3a4258; }

.send-btn {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, rgba(0,229,255,0.15), rgba(124,77,255,0.15));
  border: 1px solid rgba(0,229,255,0.2);
  border-radius: 10px;
  color: #00e5ff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(0,229,255,0.25), rgba(124,77,255,0.25));
  box-shadow: 0 0 20px rgba(0,229,255,0.12);
}

.send-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.chat-messages::-webkit-scrollbar { width: 4px; }
.chat-messages::-webkit-scrollbar-track { background: transparent; }
.chat-messages::-webkit-scrollbar-thumb { background: rgba(0,229,255,0.12); border-radius: 2px; }

@media (max-width: 768px) {
  .chat-header { padding: 14px 18px; }
  .chat-messages { padding: 18px; }
  .message-content { max-width: 85%; }
  .chat-input { padding: 14px 18px; }
  .quick-actions { flex-direction: column; }
  .quick-btn { width: 100%; }
}

@media (max-width: 480px) {
  .message-avatar { width: 32px; height: 32px; }
  .message-text { font-size: 12px; padding: 10px 14px; }
  .send-btn { width: 40px; height: 40px; }
}
</style>

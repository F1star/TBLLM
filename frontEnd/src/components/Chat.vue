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
        <label class="deep-toggle" title="深度思考（使用 ReAct 分析）">
          <input type="checkbox" v-model="deepEval">
          <span class="toggle-switch-sm"></span>
        </label>
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

      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role, { streaming: index === streamingIndex }]">
        <div class="message-avatar">
          <svg v-if="msg.role === 'assistant'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1-8.313-12.454z"/></svg>
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        </div>
        <div class="message-content">
          <div
            v-if="msg.role === 'assistant'"
            :class="['message-text', 'markdown-text', { 'streaming-text': index === streamingIndex }]"
            v-html="renderMarkdown(msg.content)"
          ></div>
          <div class="message-text" v-else>{{ msg.content }}</div>
          <div class="message-time">{{ msg.time }}</div>
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
        <button v-if="isLoading" @click="stopGeneration" class="stop-btn" title="停止生成">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="12" height="12" rx="2"/>
          </svg>
        </button>
        <button v-else @click="sendMessage" :disabled="!inputMessage.trim()" class="send-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { marked } from 'marked'

marked.setOptions({
  breaks: true,
  gfm: true,
})

const renderMarkdown = (text) => {
  if (!text) return ''
  return marked.parse(text)
}

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const streamingIndex = ref(-1)
const abortController = ref(null)
const messagesContainer = ref(null)
const inputArea = ref(null)

const stopGeneration = () => {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
}

const currentSession = ref(null)
const showSessionSelector = ref(false)
const sessions = ref([])
const sessionsLoading = ref(false)
const deepEval = ref(false)

const API_URL = 'http://localhost:5000/api/chat/stream'
const CLEAR_API_URL = 'http://localhost:5000/api/chat/clear'
const EVALUATE_API_URL = 'http://localhost:5000/api/evaluate'

const getToken = () => localStorage.getItem('token')

const formatTime = (ts) => {
  const d = ts ? new Date(ts) : new Date()
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

let scrollRAF = null
const scrollToBottom = () => {
  if (scrollRAF) return
  scrollRAF = requestAnimationFrame(() => {
    scrollRAF = null
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

  // 添加空的 assistant 消息占位，记录索引以便直接操作 reactive proxy
  const msgIdx = messages.value.length
  messages.value.push({ role: 'assistant', content: '', time: formatTime() })
  streamingIndex.value = msgIdx
  scrollToBottom()

  abortController.value = new AbortController()

  try {
    const body = { message }
    if (currentSession.value) body.session_id = currentSession.value.id
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(body),
      signal: abortController.value.signal,
    })
    if (!res.ok) throw new Error('请求失败')

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let currentEvent = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (currentEvent === 'session_created') {
            const pipeIdx = data.indexOf('|')
            if (pipeIdx !== -1) {
              const sid = parseInt(data.slice(0, pipeIdx))
              const sname = data.slice(pipeIdx + 1)
              if (sid && !currentSession.value) {
                currentSession.value = { id: sid, name: sname }
                sessions.value.unshift({ id: sid, name: sname, message_count: 1 })
                localStorage.setItem('current_session_id', sid)
                localStorage.setItem('current_session_name', sname)
              }
            }
            currentEvent = ''
          } else {
            // 通过 reactive proxy 直接更新，自动触发渲染
            messages.value[msgIdx].content += data
            scrollToBottom()
          }
        }
      }
    }
  } catch (e) {
    if (e.name === 'AbortError') {
      console.log('用户中断生成')
      // 用户手动停止，保留已生成的内容
      return
    }
    console.error('发送失败:', e)
    if (!messages.value[msgIdx]?.content) {
      messages.value[msgIdx].content = '发送消息时出现错误，请稍后重试。'
    }
  } finally {
    isLoading.value = false
    streamingIndex.value = -1
    abortController.value = null
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
    if (!res.ok) {
      if (res.status === 401) {
        window.dispatchEvent(new CustomEvent('auth-unauthorized'))
        alert('登录已过期，请重新登录')
        return
      }
      throw new Error('清除失败')
    }
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
      body: JSON.stringify({ session_id: currentSession.value.id, deep_mode: deepEval.value })
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

.deep-toggle {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.deep-toggle input {
  display: none;
}

.toggle-switch-sm {
  width: 28px;
  height: 16px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  position: relative;
  transition: all 0.3s ease;
}

.toggle-switch-sm::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 10px;
  height: 10px;
  background: #5a6275;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.deep-toggle input:checked + .toggle-switch-sm {
  background: rgba(124,77,255,0.2);
  border-color: rgba(124,77,255,0.4);
  box-shadow: 0 0 8px rgba(124,77,255,0.15);
}

.deep-toggle input:checked + .toggle-switch-sm::after {
  left: 14px;
  background: linear-gradient(135deg, #00e5ff, #7c4dff);
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
  font-family: 'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', sans-serif;
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
  font-family: 'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', sans-serif;
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
  white-space: normal;
}

.message.assistant .message-text :deep(p) {
  margin: 0 0 0.55em;
  line-height: 1.6;
}

.message.assistant .message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message.assistant .message-text :deep(strong) {
  font-weight: 600;
  color: #ffffff;
}

.message.assistant .message-text :deep(em) {
  font-style: italic;
}

.message.assistant .message-text :deep(code) {
  font-family: 'JetBrains Mono', 'PingFang SC', monospace;
  font-size: 12px;
  padding: 2px 6px;
  background: rgba(0,229,255,0.08);
  border: 1px solid rgba(0,229,255,0.12);
  border-radius: 4px;
  color: #00e5ff;
  word-break: break-all;
}

.message.assistant .message-text :deep(pre) {
  margin: 0.65em 0;
  padding: 12px 16px;
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  overflow-x: auto;
}

.message.assistant .message-text :deep(pre code) {
  background: none;
  border: none;
  padding: 0;
  color: #e8eaed;
  font-size: 12px;
  line-height: 1.6;
}

.message.assistant .message-text :deep(ul),
.message.assistant .message-text :deep(ol) {
  margin: 0.45em 0 0.65em;
  padding-left: 20px;
}

.message.assistant .message-text :deep(li) {
  margin: 0.18em 0;
  line-height: 1.6;
}

.message.assistant .message-text :deep(li > p) {
  margin: 0.2em 0;
}

.message.assistant .message-text :deep(blockquote) {
  margin: 0.65em 0;
  padding: 8px 14px;
  border-left: 3px solid rgba(0,229,255,0.3);
  background: rgba(0,229,255,0.03);
  border-radius: 0 6px 6px 0;
  color: #8892a4;
}

.message.assistant .message-text :deep(h1),
.message.assistant .message-text :deep(h2),
.message.assistant .message-text :deep(h3),
.message.assistant .message-text :deep(h4) {
  margin: 0.9em 0 0.35em;
  color: #e8eaed;
  font-weight: 600;
  line-height: 1.35;
}

.message.assistant .message-text :deep(h1) { font-size: 16px; }
.message.assistant .message-text :deep(h2) { font-size: 15px; }
.message.assistant .message-text :deep(h3) { font-size: 14px; }
.message.assistant .message-text :deep(h4) { font-size: 13px; }

.message.assistant .message-text :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.65em 0;
  font-size: 12px;
}

.message.assistant .message-text :deep(th),
.message.assistant .message-text :deep(td) {
  padding: 8px 12px;
  border: 1px solid rgba(255,255,255,0.08);
  text-align: left;
}

.message.assistant .message-text :deep(th) {
  background: rgba(0,229,255,0.06);
  color: #00e5ff;
  font-weight: 600;
}

.message.assistant .message-text :deep(tr:nth-child(even)) {
  background: rgba(255,255,255,0.02);
}

.message.assistant .message-text :deep(a) {
  color: #00e5ff;
  text-decoration: underline;
  opacity: 0.8;
}

.message.assistant .message-text :deep(a:hover) {
  opacity: 1;
}

.message.assistant .message-text :deep(hr) {
  margin: 0.8em 0;
  border: none;
  border-top: 1px solid rgba(255,255,255,0.06);
}

.streaming-text {
  word-break: break-word;
}

.streaming-text::after {
  content: none;
}

.streaming-text:empty::after,
.streaming-text :deep(p:last-child)::after,
.streaming-text :deep(li:last-child)::after {
  content: '▊';
  display: inline;
  animation: cursorBlink 1s step-end infinite;
  color: #00e5ff;
  margin-left: 2px;
}

.streaming-text :deep(li:last-child p:last-child)::after {
  content: none;
}

@keyframes cursorBlink {
  50% { opacity: 0; }
}

.message-time {
  font-size: 11px;
  color: #5a6275;
  padding: 0 4px;
}

.message.user .message-time { text-align: right; }

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
  font-family: 'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', sans-serif;
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

.stop-btn {
  width: 44px;
  height: 44px;
  background: rgba(255,23,68,0.15);
  border: 1px solid rgba(255,23,68,0.3);
  border-radius: 10px;
  color: #ff1744;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  flex-shrink: 0;
}

.stop-btn:hover {
  background: rgba(255,23,68,0.25);
  box-shadow: 0 0 20px rgba(255,23,68,0.2);
}

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

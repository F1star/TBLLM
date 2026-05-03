<template>
  <div class="history-container">
    <div class="history-header">
      <div class="header-left">
        <h2>对话历史记录</h2>
        <div class="session-info">
          <span v-if="currentSession" class="session-name">{{ currentSession.name }}</span>
          <span v-else class="no-session">未选择会话</span>
          <button @click="showSessionSelector = !showSessionSelector" class="session-select-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </button>
        </div>
      </div>
      <div class="header-actions">
        <button @click="loadHistory" class="action-btn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        </button>
        <button @click="clearHistory" class="action-btn danger">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
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

    <div v-if="loading" class="loading-state">
      <div class="loader"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="history.length === 0" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.2">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
      </svg>
      <p class="empty-title">暂无对话记录</p>
      <p class="empty-hint">开始与AI对话，记录将显示在这里</p>
    </div>

    <div v-else class="history-list">
      <div v-for="group in groupedHistory" :key="group.date" class="history-group">
        <div class="group-header">
          <span class="group-date">{{ group.date }}</span>
          <span class="group-count">{{ group.messages.length }} 条记录</span>
        </div>

        <div v-for="msg in group.messages" :key="msg.id" class="history-item" @click="viewMessage(msg)">
          <div class="msg-avatar">
            <svg v-if="msg.role === 'assistant'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1-8.313-12.454z"/></svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          </div>
          <div class="msg-content">
            <div class="msg-header">
              <span class="msg-role-label">{{ msg.role === 'user' ? '用户' : 'AI助手' }}</span>
              <span class="msg-time">{{ formatTime(msg.timestamp) }}</span>
            </div>
            <div class="msg-text">{{ truncateText(msg.content, 100) }}</div>
          </div>
          <div class="msg-actions">
            <button @click.stop="evaluateMessage(msg)" class="eval-btn" :disabled="msg.evaluating">
              {{ msg.evaluating ? '评估中' : '评估' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Message Modal -->
    <div v-if="selectedMessage" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ selectedMessage.role === 'user' ? '用户消息' : 'AI回复' }}</h3>
          <button @click="closeModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="full-message">{{ selectedMessage.content }}</div>
          <div v-if="selectedMessage.evaluation" class="eval-section">
            <h4>评估结果</h4>
            <div class="eval-grid">
              <div v-for="item in evalItems(selectedMessage.evaluation)" :key="item.label" class="eval-item">
                <span class="eval-label">{{ item.label }}</span>
                <span class="eval-score" :class="getScoreClass(item.score)">{{ item.score }}</span>
              </div>
            </div>
            <div class="overall-row" :class="getScoreClass(selectedMessage.evaluation.overall_score)">
              <span>综合评分</span>
              <span class="overall-val">{{ selectedMessage.evaluation.overall_score }}</span>
            </div>
            <div v-if="selectedMessage.evaluation.feedback" class="feedback-block">
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
const currentSession = ref(null)
const showSessionSelector = ref(false)
const sessions = ref([])
const sessionsLoading = ref(false)

const getToken = () => localStorage.getItem('token')

const formatTime = (ts) => new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })

const formatDate = (ts) => {
  const d = new Date(ts), t = new Date(), y = new Date(t)
  y.setDate(y.getDate() - 1)
  if (d.toDateString() === t.toDateString()) return '今天'
  if (d.toDateString() === y.toDateString()) return '昨天'
  return d.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })
}

const truncateText = (text, max) => !text ? '' : text.length > max ? text.substring(0, max) + '...' : text

const getScoreClass = (score) => {
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 60) return 'average'
  return 'poor'
}

const evalItems = (e) => [
  { label: '逻辑思维', score: e.logic_score },
  { label: '创造力', score: e.creativity_score },
  { label: '表达能力', score: e.expression_score },
  { label: '知识广度', score: e.knowledge_score }
]

const groupedHistory = computed(() => {
  const groups = {}
  history.value.forEach(item => {
    const date = formatDate(item.timestamp)
    if (!groups[date]) groups[date] = []
    groups[date].push(item)
  })
  return Object.keys(groups).map(date => ({ date, messages: groups[date] }))
})

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
  } catch (e) { return false }
  finally { sessionsLoading.value = false }
}

const selectSession = async (session) => {
  currentSession.value = session
  showSessionSelector.value = false
  await loadHistory()
}

const createNewSession = async () => {
  const token = getToken()
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
    }
  } catch (e) { alert('创建失败') }
}

const loadHistory = async () => {
  const token = getToken()
  if (!token) { alert('请先登录'); return }
  loading.value = true
  try {
    let url = 'http://localhost:5000/api/chat/history'
    if (currentSession.value) url += `?session_id=${currentSession.value.id}`
    const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } })
    if (!res.ok) throw new Error('获取失败')
    history.value = await res.json()
  } catch (e) { console.error(e); alert('获取历史记录失败') }
  finally { loading.value = false }
}

const clearHistory = async () => {
  const name = currentSession.value ? currentSession.value.name : '所有'
  if (!confirm(`确定要清空会话 "${name}" 的历史记录吗？`)) return
  const token = getToken()
  try {
    const body = {}
    if (currentSession.value) body.session_id = currentSession.value.id
    const res = await fetch('http://localhost:5000/api/chat/clear', {
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
    history.value = []
    alert('历史记录已清空')
  } catch (e) { alert('清除失败') }
}

const viewMessage = (msg) => { selectedMessage.value = msg }
const closeModal = () => { selectedMessage.value = null }

const evaluateMessage = async (msg) => {
  const token = getToken()
  msg.evaluating = true
  try {
    const res = await fetch('http://localhost:5000/api/evaluate', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: msg.id })
    })
    if (!res.ok) throw new Error('评估失败')
    msg.evaluation = await res.json()
  } catch (e) { alert('评估失败') }
  finally { msg.evaluating = false }
}

onMounted(() => { loadHistory() })
</script>

<style scoped>
.history-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgba(7,11,20,0.6);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  overflow: hidden;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(13,20,33,0.6);
  border-bottom: 1px solid rgba(255,255,255,0.06);
  backdrop-filter: blur(12px);
}

.header-left { display: flex; align-items: center; gap: 16px; }

.history-header h2 {
  font-family: 'Orbitron', sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: #e8eaed;
  letter-spacing: 1px;
}

.session-info { display: flex; align-items: center; gap: 6px; }
.session-name, .no-session { font-size: 11px; color: #5a6275; }
.session-select-btn { background: none; border: none; color: #5a6275; cursor: pointer; display: flex; padding: 2px; }

.header-actions { display: flex; gap: 8px; }

.action-btn {
  width: 34px; height: 34px;
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
.action-btn:hover { background: rgba(0,229,255,0.08); color: #00e5ff; }
.action-btn.danger:hover { background: rgba(255,23,68,0.08); color: #ff1744; }

/* Session Selector */
.selector-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; }
.session-selector {
  position: absolute; top: 70px; left: 24px; width: 280px;
  background: rgba(13,20,33,0.95);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(0,229,255,0.12);
  border-radius: 12px;
  z-index: 201;
  max-height: 350px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.selector-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid rgba(255,255,255,0.06); }
.selector-header h3 { font-family: 'Orbitron', sans-serif; font-size: 12px; color: #e8eaed; letter-spacing: 1px; }
.close-btn { background: none; border: none; color: #5a6275; font-size: 20px; cursor: pointer; }
.loading-sessions, .no-sessions { padding: 24px; text-align: center; color: #5a6275; font-size: 13px; }
.create-session-btn { margin-top: 12px; padding: 8px 20px; background: rgba(0,229,255,0.1); color: #00e5ff; border: 1px solid rgba(0,229,255,0.2); border-radius: 6px; font-size: 12px; cursor: pointer; font-family: 'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', sans-serif; }
.sessions-list { overflow-y: auto; padding: 8px; }
.session-item { padding: 12px 16px; border-radius: 8px; cursor: pointer; transition: all 0.2s; margin-bottom: 4px; }
.session-item:hover { background: rgba(255,255,255,0.04); }
.session-item.active { background: rgba(0,229,255,0.06); border: 1px solid rgba(0,229,255,0.12); }
.session-item-name { font-size: 13px; color: #e8eaed; font-weight: 500; margin-bottom: 4px; }
.session-item-meta { font-size: 11px; color: #5a6275; }

.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 300px; color: #5a6275; font-size: 13px; gap: 12px; }

.loader {
  width: 28px; height: 28px;
  border: 2px solid rgba(0,229,255,0.1);
  border-top-color: #00e5ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 300px; text-align: center; gap: 12px;
}
.empty-title { font-size: 16px; font-weight: 600; color: #e8eaed; }
.empty-hint { font-size: 13px; color: #5a6275; }

.history-list { flex: 1; overflow-y: auto; padding: 24px; }

.history-group { margin-bottom: 28px; }

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: rgba(0,229,255,0.05);
  border: 1px solid rgba(0,229,255,0.08);
  border-radius: 8px;
  margin-bottom: 12px;
}
.group-date { font-family: 'Orbitron', sans-serif; font-size: 12px; color: #00e5ff; letter-spacing: 1px; }
.group-count { font-size: 11px; color: #5a6275; }

.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s;
}
.history-item:hover {
  background: rgba(255,255,255,0.03);
  border-color: rgba(0,229,255,0.1);
  transform: translateX(4px);
}

.msg-avatar {
  width: 36px; height: 36px;
  background: rgba(0,229,255,0.08);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: #00e5ff;
  flex-shrink: 0;
}

.msg-content { flex: 1; min-width: 0; }

.msg-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.msg-role-label { font-size: 12px; font-weight: 600; color: #00e5ff; }
.msg-time { font-size: 11px; color: #5a6275; }
.msg-text { font-size: 13px; color: #8892a4; line-height: 1.5; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.msg-actions { flex-shrink: 0; }

.eval-btn {
  padding: 6px 14px;
  background: rgba(0,229,255,0.08);
  border: 1px solid rgba(0,229,255,0.15);
  border-radius: 6px;
  color: #00e5ff;
  font-size: 11px;
  font-family: 'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  cursor: pointer;
  transition: all 0.3s;
}
.eval-btn:hover:not(:disabled) { background: rgba(0,229,255,0.15); }
.eval-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 20px;
}

.modal {
  background: rgba(13,20,33,0.96);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(0,229,255,0.1);
  border-radius: 16px;
  max-width: 640px;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.modal-header h3 { font-family: 'Orbitron', sans-serif; font-size: 13px; color: #e8eaed; letter-spacing: 0.5px; }

.modal-body { padding: 24px; }

.full-message {
  padding: 16px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  font-size: 13px; line-height: 1.8; color: #e8eaed;
  white-space: pre-wrap; word-wrap: break-word;
  margin-bottom: 24px;
}

.eval-section h4 { font-family: 'Orbitron', sans-serif; font-size: 12px; color: #e8eaed; letter-spacing: 0.5px; margin-bottom: 12px; }

.eval-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px; }

.eval-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
}
.eval-label { font-size: 12px; color: #5a6275; }
.eval-score { font-family: 'Orbitron', sans-serif; font-size: 18px; font-weight: 700; }
.eval-score.excellent { color: #00e676; }
.eval-score.good { color: #00e5ff; }
.eval-score.average { color: #ffab00; }
.eval-score.poor { color: #ff1744; }

.overall-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(0,229,255,0.1), rgba(124,77,255,0.1));
  border: 1px solid rgba(0,229,255,0.15);
  border-radius: 10px;
  margin-bottom: 20px;
  font-size: 14px; font-weight: 600; color: #e8eaed;
}
.overall-val { font-family: 'Orbitron', sans-serif; font-size: 24px; font-weight: 700; color: #00e5ff; }

.feedback-block h4 { font-size: 12px; color: #e8eaed; margin-bottom: 8px; }
.feedback-block p {
  font-size: 13px; line-height: 1.7; color: #8892a4;
  padding: 14px;
  background: rgba(255,255,255,0.02);
  border-left: 2px solid rgba(0,229,255,0.3);
  border-radius: 0 8px 8px 0;
}

.history-list::-webkit-scrollbar { width: 4px; }
.history-list::-webkit-scrollbar-thumb { background: rgba(0,229,255,0.1); border-radius: 2px; }

@media (max-width: 768px) {
  .history-header { padding: 14px 18px; }
  .history-list { padding: 18px; }
  .eval-grid { grid-template-columns: 1fr; }
}

@media (max-width: 480px) {
  .history-item { flex-direction: column; align-items: flex-start; }
  .msg-actions { width: 100%; }
  .eval-btn { width: 100%; text-align: center; }
}
</style>

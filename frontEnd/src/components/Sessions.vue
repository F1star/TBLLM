<template>
  <div class="sessions-container">
    <div class="sessions-header">
      <h2>会话管理</h2>
      <button class="create-btn" @click="showCreateModal = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        新建会话
      </button>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loader"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadSessions" class="retry-btn">重试</button>
    </div>

    <div v-else-if="sessions.length === 0" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      <h3>还没有会话</h3>
      <p>创建一个新会话来开始对话吧</p>
      <button class="create-btn" @click="showCreateModal = true">创建会话</button>
    </div>

    <div v-else class="sessions-grid">
      <div v-for="session in sessions" :key="session.id" class="session-card">
        <div class="card-accent"></div>
        <div class="session-card-header">
          <div class="session-title">
            <input
              v-if="session.editing"
              v-model="session.editName"
              @keyup.enter="saveSessionName(session)"
              @blur="saveSessionName(session)"
              @keyup.esc="cancelEdit(session)"
              class="title-input"
              type="text"
              placeholder="会话标题"
            />
            <h3 v-else @click="startEdit(session)">{{ session.name }}</h3>
          </div>
          <div class="session-actions">
            <button @click="startEdit(session)" class="icon-btn" title="编辑">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </button>
            <button @click="deleteSession(session)" class="icon-btn danger" title="删除">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
        </div>

        <div class="session-stats">
          <div class="stat-item">
            <span class="stat-label">消息数</span>
            <span class="stat-val">{{ session.message_count }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">创建</span>
            <span class="stat-val">{{ formatDate(session.created_at) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">更新</span>
            <span class="stat-val">{{ formatDate(session.updated_at) }}</span>
          </div>
        </div>

        <div class="session-actions-row">
          <button class="action-btn primary" @click="openSession(session)">打开</button>
          <button class="action-btn" @click="viewSessionMessages(session)">消息</button>
          <button class="action-btn" @click="evaluateSession(session)">评估</button>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>创建新会话</h3>
          <button @click="showCreateModal = false" class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="session-name">会话名称</label>
            <input id="session-name" v-model="newSessionName" type="text" placeholder="请输入会话名称" @keyup.enter="confirmCreateSession" />
            <p class="hint">留空将使用第一条消息自动生成标题</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="modal-btn secondary" @click="showCreateModal = false">取消</button>
          <button class="modal-btn primary" @click="confirmCreateSession">创建</button>
        </div>
      </div>
    </div>

    <!-- Messages Modal -->
    <div v-if="showMessagesModal" class="modal-overlay" @click.self="showMessagesModal = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>{{ selectedSession ? selectedSession.name : '' }}</h3>
          <button @click="showMessagesModal = false" class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
          <div v-if="messagesLoading" class="loading-state"><div class="loader"></div></div>
          <div v-else-if="sessionMessages.length === 0" class="empty-inner">该会话还没有消息</div>
          <div v-else class="messages-list">
            <div v-for="msg in sessionMessages" :key="msg.id" class="msg-item">
              <div class="msg-role">{{ msg.role === 'user' ? '用户' : 'AI助手' }}</div>
              <div class="msg-content">{{ msg.content }}</div>
              <div class="msg-time">{{ formatDateTime(msg.timestamp) }}</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="modal-btn secondary" @click="showMessagesModal = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Sessions',
  data() {
    return {
      sessions: [], loading: false, error: null,
      showCreateModal: false, newSessionName: '',
      showMessagesModal: false, selectedSession: null, sessionMessages: [], messagesLoading: false
    };
  },
  mounted() { this.loadSessions(); },
  methods: {
    async loadSessions() {
      this.loading = true; this.error = null;
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('http://localhost:5050/api/sessions', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          this.sessions = (await res.json()).map(s => ({ ...s, editing: false, editName: s.name }));
        } else {
          const e = await res.json();
          this.error = e.error || '加载失败';
        }
      } catch (err) { this.error = '网络错误'; }
      finally { this.loading = false; }
    },
    async confirmCreateSession() {
      const token = localStorage.getItem('token');
      try {
        const res = await fetch('http://localhost:5050/api/sessions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ name: this.newSessionName })
        });
        if (res.ok) {
          const session = await res.json();
          this.sessions.unshift({ ...session, editing: false, editName: session.name });
          this.showCreateModal = false;
          this.newSessionName = '';
        } else {
          const e = await res.json();
          alert('创建失败: ' + (e.error || '未知错误'));
        }
      } catch (err) { alert('创建失败'); }
    },
    startEdit(session) {
      session.editing = true;
      session.editName = session.name;
      this.$nextTick(() => { const el = this.$el.querySelector('.title-input'); if (el) el.focus(); });
    },
    async saveSessionName(session) {
      if (!session.editName.trim()) session.editName = session.name;
      if (session.editName === session.name) { session.editing = false; return; }
      const token = localStorage.getItem('token');
      try {
        const res = await fetch(`http://localhost:5050/api/sessions/${session.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ name: session.editName })
        });
        if (res.ok) {
          session.name = (await res.json()).name;
          session.editing = false;
        } else { session.editing = false; }
      } catch (err) { session.editing = false; }
    },
    cancelEdit(session) { session.editing = false; },
    async deleteSession(session) {
      if (!confirm(`确定要删除 "${session.name}" 吗？`)) return;
      const token = localStorage.getItem('token');
      try {
        const res = await fetch(`http://localhost:5050/api/sessions/${session.id}`, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ delete_messages: false })
        });
        if (res.ok) { this.sessions = this.sessions.filter(s => s.id !== session.id); }
        else if (res.status === 401) {
          window.dispatchEvent(new CustomEvent('auth-unauthorized'))
          alert('登录已过期，请重新登录')
        }
        else { const e = await res.json(); alert('删除失败: ' + (e.error || '未知错误')); }
      } catch (err) { alert('删除失败'); }
    },
    openSession(session) {
      this.$parent.currentPage = 'chat';
      localStorage.setItem('current_session_id', session.id);
      localStorage.setItem('current_session_name', session.name);
      window.dispatchEvent(new CustomEvent('session-changed'));
    },
    async viewSessionMessages(session) {
      this.selectedSession = session;
      this.showMessagesModal = true;
      this.sessionMessages = [];
      this.messagesLoading = true;
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`http://localhost:5050/api/chat/history?session_id=${session.id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) this.sessionMessages = await res.json();
      } catch (err) { alert('加载失败'); }
      finally { this.messagesLoading = false; }
    },
    async evaluateSession(session) {
      if (!confirm(`确定要评估 "${session.name}" 吗？`)) return;
      const token = localStorage.getItem('token');
      try {
        const res = await fetch('http://localhost:5050/api/evaluate', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: session.id })
        });
        if (!res.ok) throw new Error('评估失败');
        const r = await res.json();
        alert(`评估完成！\n综合得分: ${r.overall_score}\n\n反馈: ${r.feedback}`);
      } catch (err) { alert('评估失败: ' + err.message); }
    },
    formatDate(ts) {
      if (!ts) return '-';
      const d = new Date(ts);
      return d.toLocaleDateString('zh-CN');
    },
    formatDateTime(ts) {
      if (!ts) return '-';
      return new Date(ts).toLocaleString('zh-CN');
    }
  }
};
</script>

<style scoped>
.sessions-container {
  padding: 0;
  max-width: 1200px;
  margin: 0 auto;
}

.sessions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.sessions-header h2 {
  font-family: 'Orbitron', sans-serif;
  font-size: 16px;
  font-weight: 600;
  color: #e8eaed;
  letter-spacing: 1px;
}

.create-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: rgba(0,229,255,0.08);
  color: #00e5ff;
  border: 1px solid rgba(0,229,255,0.2);
  border-radius: 8px;
  font-size: 12px;
  font-family: 'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.create-btn:hover {
  background: rgba(0,229,255,0.15);
  box-shadow: 0 0 20px rgba(0,229,255,0.1);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: #5a6275;
  font-size: 13px;
  gap: 16px;
}

.loader {
  width: 32px;
  height: 32px;
  border: 2px solid rgba(0,229,255,0.1);
  border-top-color: #00e5ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.error-state {
  text-align: center;
  padding: 40px;
  background: rgba(255,23,68,0.06);
  border: 1px solid rgba(255,23,68,0.12);
  border-radius: 12px;
  color: #ff1744;
  font-size: 13px;
}

.retry-btn {
  margin-top: 12px;
  padding: 8px 20px;
  background: rgba(255,23,68,0.1);
  color: #ff1744;
  border: 1px solid rgba(255,23,68,0.2);
  border-radius: 6px;
  cursor: pointer;
  font-family: 'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 12px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 20px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  text-align: center;
  gap: 12px;
}

.empty-state h3 {
  font-family: 'Orbitron', sans-serif;
  font-size: 16px;
  color: #e8eaed;
  letter-spacing: 1px;
}

.empty-state p { font-size: 13px; color: #5a6275; }

.sessions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.session-card {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  padding: 20px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.session-card:hover {
  border-color: rgba(0,229,255,0.15);
  background: rgba(255,255,255,0.03);
  box-shadow: 0 0 30px rgba(0,229,255,0.04);
  transform: translateY(-2px);
}

.card-accent {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(0,229,255,0.3), transparent);
}

.session-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.session-title { flex: 1; margin-right: 12px; }

.title-input {
  width: 100%;
  padding: 8px 12px;
  background: rgba(0,229,255,0.06);
  border: 1px solid rgba(0,229,255,0.25);
  border-radius: 6px;
  color: #e8eaed;
  font-family: 'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  outline: none;
}

.session-title h3 {
  font-size: 15px;
  font-weight: 600;
  color: #e8eaed;
  cursor: pointer;
  padding: 4px 0;
  border-bottom: 1px dashed transparent;
  transition: border-color 0.2s;
}

.session-title h3:hover { border-bottom-color: #3a4258; }

.session-actions { display: flex; gap: 6px; }

.icon-btn {
  width: 32px; height: 32px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 6px;
  color: #5a6275;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: rgba(0,229,255,0.08);
  color: #00e5ff;
  border-color: rgba(0,229,255,0.2);
}

.icon-btn.danger:hover {
  background: rgba(255,23,68,0.08);
  color: #ff1744;
  border-color: rgba(255,23,68,0.2);
}

.session-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 12px;
  background: rgba(255,255,255,0.02);
  border-radius: 8px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 4px;
}

.stat-label {
  font-size: 10px;
  color: #5a6275;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-val {
  font-size: 13px;
  font-weight: 500;
  color: #8892a4;
}

.session-actions-row {
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1;
  padding: 8px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 6px;
  color: #8892a4;
  font-size: 11px;
  font-family: 'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  cursor: pointer;
  transition: all 0.3s;
}

.action-btn:hover {
  border-color: rgba(255,255,255,0.15);
  color: #e8eaed;
}

.action-btn.primary {
  background: rgba(0,229,255,0.08);
  color: #00e5ff;
  border-color: rgba(0,229,255,0.15);
}

.action-btn.primary:hover {
  background: rgba(0,229,255,0.15);
  box-shadow: 0 0 16px rgba(0,229,255,0.08);
}

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: rgba(13,20,33,0.96);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(0,229,255,0.1);
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.modal-lg { max-width: 700px; max-height: 80vh; display: flex; flex-direction: column; }

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.modal-header h3 {
  font-family: 'Orbitron', sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: #e8eaed;
  letter-spacing: 0.5px;
}

.modal-close {
  background: none;
  border: none;
  color: #5a6275;
  font-size: 24px;
  cursor: pointer;
  transition: color 0.2s;
}

.modal-close:hover { color: #e8eaed; }

.modal-body { padding: 24px; overflow-y: auto; }

.form-group { margin-bottom: 20px; }

.form-group label {
  display: block;
  font-size: 11px;
  color: #5a6275;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  color: #e8eaed;
  font-family: 'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 13px;
  outline: none;
  transition: border-color 0.3s;
}

.form-group input:focus {
  border-color: rgba(0,229,255,0.3);
}

.hint { font-size: 11px; color: #5a6275; margin-top: 8px; }

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid rgba(255,255,255,0.06);
}

.modal-btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 12px;
  font-family: 'JetBrains Mono', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 500;
}

.modal-btn.secondary {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  color: #5a6275;
}

.modal-btn.secondary:hover { background: rgba(255,255,255,0.06); }

.modal-btn.primary {
  background: rgba(0,229,255,0.1);
  border: 1px solid rgba(0,229,255,0.2);
  color: #00e5ff;
}

.modal-btn.primary:hover {
  background: rgba(0,229,255,0.18);
  box-shadow: 0 0 16px rgba(0,229,255,0.08);
}

.messages-list {
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.msg-item {
  padding: 16px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
}

.msg-role {
  font-size: 11px;
  font-weight: 600;
  color: #00e5ff;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.msg-content {
  font-size: 13px;
  color: #e8eaed;
  line-height: 1.6;
  white-space: pre-wrap;
  margin-bottom: 8px;
}

.msg-time {
  font-size: 11px;
  color: #5a6275;
  text-align: right;
}

.empty-inner {
  text-align: center;
  padding: 40px;
  color: #5a6275;
  font-size: 13px;
}

.messages-list::-webkit-scrollbar { width: 4px; }
.messages-list::-webkit-scrollbar-thumb { background: rgba(0,229,255,0.1); border-radius: 2px; }

@media (max-width: 768px) {
  .sessions-grid { grid-template-columns: 1fr; }
  .session-stats { grid-template-columns: repeat(2, 1fr); }
  .session-actions-row { flex-direction: column; }
}
</style>

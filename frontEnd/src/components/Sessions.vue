<template>
  <div class="sessions-container">
    <div class="sessions-header">
      <h2>会话管理</h2>
      <button class="create-session-btn" @click="createNewSession">
        <span>+ 新建会话</span>
      </button>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="loadSessions">重试</button>
    </div>

    <div v-else-if="sessions.length === 0" class="empty-state">
      <div class="empty-icon">💬</div>
      <h3>还没有会话</h3>
      <p>创建一个新会话来开始对话吧</p>
      <button class="create-btn" @click="createNewSession">创建会话</button>
    </div>

    <div v-else class="sessions-grid">
      <div v-for="session in sessions" :key="session.id" class="session-card">
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
            <h3 v-else @click="startEdit(session)" class="title-text">
              {{ session.name }}
            </h3>
          </div>
          <div class="session-actions">
            <button class="icon-btn" @click="startEdit(session)" title="编辑标题">
              ✏️
            </button>
            <button class="icon-btn" @click="deleteSession(session)" title="删除会话">
              🗑️
            </button>
          </div>
        </div>

        <div class="session-stats">
          <div class="stat">
            <span class="stat-label">消息数</span>
            <span class="stat-value">{{ session.message_count }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">创建时间</span>
            <span class="stat-value">{{ formatDate(session.created_at) }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">最后更新</span>
            <span class="stat-value">{{ formatDate(session.updated_at) }}</span>
          </div>
        </div>

        <div class="session-actions-row">
          <button class="action-btn primary" @click="openSession(session)">
            打开会话
          </button>
          <button class="action-btn" @click="viewSessionMessages(session)">
            查看消息
          </button>
          <button class="action-btn" @click="evaluateSession(session)">
            评估会话
          </button>
        </div>
      </div>
    </div>

    <!-- 创建会话模态框 -->
    <div v-if="showCreateModal" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h3>创建新会话</h3>
          <button class="close-btn" @click="showCreateModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="session-name">会话名称</label>
            <input
              id="session-name"
              v-model="newSessionName"
              type="text"
              placeholder="请输入会话名称"
              @keyup.enter="confirmCreateSession"
            />
            <p class="hint">如果不填，将使用第一条消息自动生成标题</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCreateModal = false">
            取消
          </button>
          <button class="btn-primary" @click="confirmCreateSession">
            创建
          </button>
        </div>
      </div>
    </div>

    <!-- 查看消息模态框 -->
    <div v-if="showMessagesModal" class="modal-overlay">
      <div class="modal modal-large">
        <div class="modal-header">
          <h3>会话消息：{{ selectedSession ? selectedSession.name : '' }}</h3>
          <button class="close-btn" @click="showMessagesModal = false">×</button>
        </div>
        <div class="modal-body">
          <div v-if="messagesLoading" class="loading-messages">
            <div class="spinner"></div>
            <p>加载消息中...</p>
          </div>
          <div v-else-if="sessionMessages.length === 0" class="empty-messages">
            <p>该会话还没有消息</p>
          </div>
          <div v-else class="messages-list">
            <div v-for="msg in sessionMessages" :key="msg.id" class="message-item">
              <div class="message-role">{{ msg.role === 'user' ? '👤 用户' : '🤖 AI助手' }}</div>
              <div class="message-content">{{ msg.content }}</div>
              <div class="message-time">{{ formatDateTime(msg.timestamp) }}</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showMessagesModal = false">关闭</button>
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
      sessions: [],
      loading: false,
      error: null,
      showCreateModal: false,
      newSessionName: '',
      // 消息查看模态框
      showMessagesModal: false,
      selectedSession: null,
      sessionMessages: [],
      messagesLoading: false,
      // 评估相关
      evaluateLoading: false,
    };
  },
  mounted() {
    this.loadSessions();
  },
  methods: {
    async loadSessions() {
      this.loading = true;
      this.error = null;
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('http://localhost:5000/api/sessions', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          this.sessions = data.map(session => ({
            ...session,
            editing: false,
            editName: session.name
          }));
        } else {
          const error = await response.json();
          this.error = error.error || '加载会话失败';
        }
      } catch (err) {
        console.error('加载会话失败:', err);
        this.error = '网络错误，请检查连接';
      } finally {
        this.loading = false;
      }
    },

    createNewSession() {
      this.newSessionName = '';
      this.showCreateModal = true;
    },

    async confirmCreateSession() {
      if (!this.newSessionName.trim()) {
        this.newSessionName = '';
      }

      const token = localStorage.getItem('token');
      try {
        const response = await fetch('http://localhost:5000/api/sessions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ name: this.newSessionName })
        });

        if (response.ok) {
          const session = await response.json();
          this.sessions.unshift({
            ...session,
            editing: false,
            editName: session.name
          });
          this.showCreateModal = false;
          alert('会话创建成功！');
        } else {
          const error = await response.json();
          alert('创建失败: ' + (error.error || '未知错误'));
        }
      } catch (err) {
        console.error('创建会话失败:', err);
        alert('创建失败，请稍后重试');
      }
    },

    startEdit(session) {
      session.editing = true;
      session.editName = session.name;
      // 下一个tick聚焦输入框
      this.$nextTick(() => {
        const input = this.$el.querySelector('.title-input');
        if (input) input.focus();
      });
    },

    async saveSessionName(session) {
      if (!session.editName.trim()) {
        session.editName = session.name;
      }

      if (session.editName === session.name) {
        session.editing = false;
        return;
      }

      const token = localStorage.getItem('token');
      try {
        const response = await fetch(`http://localhost:5000/api/sessions/${session.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ name: session.editName })
        });

        if (response.ok) {
          const updatedSession = await response.json();
          session.name = updatedSession.name;
          session.editing = false;
          alert('会话名称已更新');
        } else {
          const error = await response.json();
          alert('更新失败: ' + (error.error || '未知错误'));
          session.editing = false;
        }
      } catch (err) {
        console.error('更新会话失败:', err);
        alert('更新失败，请稍后重试');
        session.editing = false;
      }
    },

    cancelEdit(session) {
      session.editing = false;
    },

    async deleteSession(session) {
      if (!confirm(`确定要删除会话 "${session.name}" 吗？`)) {
        return;
      }

      const token = localStorage.getItem('token');
      try {
        const response = await fetch(`http://localhost:5000/api/sessions/${session.id}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ delete_messages: false })
        });

        if (response.ok) {
          this.sessions = this.sessions.filter(s => s.id !== session.id);
          alert('会话删除成功');
        } else {
          const error = await response.json();
          alert('删除失败: ' + (error.error || '未知错误'));
        }
      } catch (err) {
        console.error('删除会话失败:', err);
        alert('删除失败，请稍后重试');
      }
    },

    openSession(session) {
      // 切换到聊天页面并设置当前会话
      this.$parent.currentPage = 'chat';
      // 传递会话ID到聊天组件，需要全局状态管理或事件总线
      // 暂时使用简单方式：存储到localStorage
      localStorage.setItem('current_session_id', session.id);
      localStorage.setItem('current_session_name', session.name);
      // 触发自定义事件，通知聊天组件会话已切换
      window.dispatchEvent(new CustomEvent('session-changed', {
        detail: { sessionId: session.id, sessionName: session.name }
      }));
      alert(`已切换到会话 "${session.name}"，请在聊天页面开始对话`);
    },

    async viewSessionMessages(session) {
      this.selectedSession = session
      this.showMessagesModal = true
      this.sessionMessages = []
      this.messagesLoading = true

      try {
        const token = localStorage.getItem('token')
        const response = await fetch(`http://localhost:5000/api/chat/history?session_id=${session.id}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const data = await response.json()
          this.sessionMessages = data
        } else {
          const error = await response.json()
          alert('加载消息失败: ' + (error.error || '未知错误'))
        }
      } catch (err) {
        console.error('加载消息失败:', err)
        alert('网络错误，请检查连接')
      } finally {
        this.messagesLoading = false
      }
    },

    formatDateTime(timestamp) {
      if (!timestamp) return '-'
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN')
    },

    async evaluateSession(session) {
      if (!confirm(`确定要评估会话 "${session.name}" 吗？`)) {
        return
      }

      this.evaluateLoading = true
      try {
        const token = localStorage.getItem('token')
        const response = await fetch('http://localhost:5000/api/evaluate', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_id: session.id
          })
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.error || '评估失败')
        }

        const result = await response.json()

        // 显示评估结果
        const scoreText = `逻辑思维: ${result.logic_score}\n创造力: ${result.creativity_score}\n表达能力: ${result.expression_score}\n知识掌握: ${result.knowledge_score}\n综合得分: ${result.overall_score}\n\n反馈: ${result.feedback}`
        alert(`评估完成！\n\n${scoreText}`)
      } catch (err) {
        console.error('评估失败:', err)
        alert('评估失败: ' + err.message)
      } finally {
        this.evaluateLoading = false
      }
    },

    formatDate(dateString) {
      if (!dateString) return '-';
      const date = new Date(dateString);
      return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }
  }
};
</script>

<style scoped>
.sessions-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.sessions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.sessions-header h2 {
  font-size: 28px;
  color: #1e293b;
}

.create-session-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.create-session-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.loading {
  text-align: center;
  padding: 60px 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  margin: 0 auto 16px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error {
  text-align: center;
  padding: 40px;
  background: #fee2e2;
  border-radius: 12px;
  color: #dc2626;
}

.error button {
  margin-top: 16px;
  padding: 8px 16px;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 24px;
  color: #1e293b;
  margin-bottom: 12px;
}

.empty-state p {
  color: #64748b;
  margin-bottom: 24px;
}

.create-btn {
  padding: 12px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}

.sessions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
}

.session-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.session-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.session-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.session-title {
  flex: 1;
  margin-right: 12px;
}

.title-input {
  width: 100%;
  padding: 8px 12px;
  border: 2px solid #667eea;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  outline: none;
}

.title-text {
  font-size: 20px;
  color: #1e293b;
  margin: 0;
  cursor: pointer;
  padding: 4px 0;
  border-bottom: 2px dashed transparent;
}

.title-text:hover {
  border-bottom-color: #cbd5e1;
}

.session-actions {
  display: flex;
  gap: 8px;
}

.icon-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: background 0.2s;
}

.icon-btn:hover {
  background: #f1f5f9;
}

.session-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
  font-weight: 500;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.session-actions-row {
  display: flex;
  gap: 12px;
  margin-top: auto;
}

.action-btn {
  flex: 1;
  padding: 10px 16px;
  background: #f1f5f9;
  color: #475569;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #e2e8f0;
  transform: translateY(-2px);
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.action-btn.primary:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  margin: 0;
  color: #1e293b;
  font-size: 20px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #64748b;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.close-btn:hover {
  background: #f1f5f9;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #475569;
  font-weight: 600;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 16px;
  transition: border 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.hint {
  font-size: 13px;
  color: #94a3b8;
  margin-top: 8px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 24px;
  border-top: 1px solid #e2e8f0;
}

.btn-secondary {
  padding: 10px 20px;
  background: #f1f5f9;
  color: #475569;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

/* 消息模态框样式 */
.modal-large {
  max-width: 800px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.loading-messages {
  text-align: center;
  padding: 40px;
}

.empty-messages {
  text-align: center;
  padding: 40px;
  color: #64748b;
}

.messages-list {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 10px;
}

.message-item {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.message-role {
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
  font-size: 14px;
}

.message-content {
  color: #1e293b;
  line-height: 1.6;
  margin-bottom: 8px;
  white-space: pre-wrap;
}

.message-time {
  font-size: 12px;
  color: #94a3b8;
  text-align: right;
}

@media (max-width: 768px) {
  .sessions-grid {
    grid-template-columns: 1fr;
  }

  .session-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .session-actions-row {
    flex-direction: column;
  }
}
</style>
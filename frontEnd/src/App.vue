<template>
  <div class="app">
    <div v-if="isLoggedIn" class="main-layout">
      <aside class="sidebar">
        <div class="sidebar-header">
          <div class="logo">
            <span class="logo-icon">📊</span>
            <span class="logo-text">综合能力评价系统</span>
          </div>
        </div>
        
        <nav class="sidebar-nav">
          <a href="#" :class="['nav-item', { active: currentPage === 'dashboard' }]" @click.prevent="currentPage = 'dashboard'">
            <span class="nav-icon">🏠</span>
            <span class="nav-text">仪表盘</span>
          </a>
          <a href="#" :class="['nav-item', { active: currentPage === 'sessions' }]" @click.prevent="currentPage = 'sessions'">
            <span class="nav-icon">💬</span>
            <span class="nav-text">会话管理</span>
          </a>
          <a href="#" :class="['nav-item', { active: currentPage === 'evaluations' }]" @click.prevent="currentPage = 'evaluations'">
            <span class="nav-icon">📊</span>
            <span class="nav-text">评分记录</span>
          </a>
          <a href="#" :class="['nav-item', { active: currentPage === 'professional-assessment' }]" @click.prevent="currentPage = 'professional-assessment'">
            <span class="nav-icon">📝</span>
            <span class="nav-text">专业测评</span>
          </a>
          <a href="#" :class="['nav-item', { active: currentPage === 'files' }]" @click.prevent="currentPage = 'files'">
            <span class="nav-icon">📁</span>
            <span class="nav-text">文件管理</span>
          </a>
          <a href="#" :class="['nav-item', { active: currentPage === 'chat' }]" @click.prevent="currentPage = 'chat'">
            <span class="nav-icon">💬</span>
            <span class="nav-text">AI对话</span>
          </a>
          <a href="#" :class="['nav-item', { active: currentPage === 'settings' }]" @click.prevent="currentPage = 'settings'">
            <span class="nav-icon">⚙️</span>
            <span class="nav-text">设置</span>
          </a>
        </nav>
        
        <div class="sidebar-footer">
          <div class="user-info">
            <div class="user-avatar">{{ username.charAt(0).toUpperCase() }}</div>
            <div class="user-details">
              <div class="user-name">{{ username }}</div>
              <div class="user-role">学生</div>
            </div>
          </div>
          <button @click="logout" class="logout-btn">
            <span>退出登录</span>
          </button>
        </div>
      </aside>
      
      <main class="main-content">
        <header class="top-header">
          <div class="header-title">
            <h1>{{ pageTitle }}</h1>
          </div>
          <div class="header-actions">
            <button class="action-btn">
              <span>🔔</span>
            </button>
            <button class="action-btn">
              <span>❓</span>
            </button>
          </div>
        </header>
        
        <div class="content-area">
          <div v-if="currentPage === 'dashboard'" class="dashboard-content">
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-info">
                  <div class="stat-value">{{ latestEvaluation ? latestEvaluation.overall_score : '-' }}</div>
                  <div class="stat-label">综合评分</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">🧠</div>
                <div class="stat-info">
                  <div class="stat-value" :class="latestEvaluation ? getScoreClass(latestEvaluation.logic_score) : ''">
                    {{ latestEvaluation ? latestEvaluation.logic_score : '-' }}
                  </div>
                  <div class="stat-label">逻辑思维</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">💡</div>
                <div class="stat-info">
                  <div class="stat-value" :class="latestEvaluation ? getScoreClass(latestEvaluation.creativity_score) : ''">
                    {{ latestEvaluation ? latestEvaluation.creativity_score : '-' }}
                  </div>
                  <div class="stat-label">创造力</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">📝</div>
                <div class="stat-info">
                  <div class="stat-value" :class="latestEvaluation ? getScoreClass(latestEvaluation.expression_score) : ''">
                    {{ latestEvaluation ? latestEvaluation.expression_score : '-' }}
                  </div>
                  <div class="stat-label">表达能力</div>
                </div>
              </div>
            </div>
            
            <div class="content-grid">
              <div class="content-card">
                <h3>能力评估</h3>
                <div v-if="latestEvaluation" class="evaluation-details">
                  <div class="evaluation-item">
                    <span class="item-label">知识广度</span>
                    <span class="item-score" :class="getScoreClass(latestEvaluation.knowledge_score)">
                      {{ latestEvaluation.knowledge_score }}
                    </span>
                  </div>
                  <div class="evaluation-item">
                    <span class="item-label">反馈意见</span>
                    <span class="item-feedback">{{ latestEvaluation.feedback }}</span>
                  </div>
                  <div class="evaluation-time">
                    评分时间：{{ new Date(latestEvaluation.timestamp).toLocaleString('zh-CN') }}
                  </div>
                  <div class="evaluation-actions">
                    <button @click="startEvaluation" class="reevaluate-btn" :disabled="isEvaluating">
                      <span v-if="!isEvaluating">🔄 重新评估</span>
                      <span v-else>⏳ 评估中...</span>
                    </button>
                  </div>
                </div>
                <div v-else class="no-evaluation">
                  <div class="no-evaluation-icon">📊</div>
                  <p>暂无评分记录</p>
                  <button @click="startEvaluation" class="evaluate-btn" :disabled="isEvaluating">
                    <span v-if="!isEvaluating">开始评估</span>
                    <span v-else>评估中...</span>
                  </button>
                </div>
              </div>
              
              <div class="content-card">
                <h3>能力雷达图</h3>
                <div v-if="latestEvaluation" class="radar-chart-wrapper">
                  <RadarChart :evaluation="latestEvaluation" />
                </div>
                <div v-else class="chart-placeholder">
                  <div class="chart-placeholder-text">暂无评分数据</div>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else-if="currentPage === 'chat'" class="chat-content">
            <Chat />
          </div>

          <div v-else-if="currentPage === 'sessions'" class="sessions-content">
            <Sessions />
          </div>

          <div v-else-if="currentPage === 'history'" class="history-content">
            <History />
          </div>
          
          <div v-else-if="currentPage === 'evaluations'" class="evaluations-content">
            <Evaluations />
          </div>

          <div v-else-if="currentPage === 'professional-assessment'" class="professional-assessment-content">
            <ProfessionalAssessment />
          </div>

          <div v-else-if="currentPage === 'files'" class="files-content">
            <FileUpload @useForEvaluation="handleUseFileForEvaluation" />
            <div v-if="fileIds.length > 0" class="file-ids-list">
              <h4>当前评估文件列表</h4>
              <div class="file-ids-content">
                <span v-for="id in fileIds" :key="id" class="file-id-tag">
                  文件 ID: {{ id }}
                  <button @click="fileIds = fileIds.filter(fid => fid !== id)" class="remove-tag-btn">×</button>
                </span>
                <button @click="clearFileIds" class="clear-btn">清空</button>
              </div>
            </div>
          </div>
          
          <div v-else-if="currentPage === 'settings'" class="settings-content">
            <div class="settings-container">
              <div class="settings-card">
                <h3>账户设置</h3>
                
                <div class="setting-item">
                  <label>用户名</label>
                  <div class="user-info-display">{{ username }}</div>
                </div>
                
                <div class="setting-section">
                  <h4>修改密码</h4>
                  <form @submit.prevent="changePassword" class="password-form">
                    <div class="form-group">
                      <label for="currentPassword">当前密码</label>
                      <input 
                        type="password" 
                        id="currentPassword" 
                        v-model="passwordForm.currentPassword" 
                        placeholder="请输入当前密码"
                        required
                      />
                    </div>
                    <div class="form-group">
                      <label for="newPassword">新密码</label>
                      <input 
                        type="password" 
                        id="newPassword" 
                        v-model="passwordForm.newPassword" 
                        placeholder="请输入新密码"
                        required
                        minlength="6"
                      />
                    </div>
                    <div class="form-group">
                      <label for="confirmPassword">确认新密码</label>
                      <input 
                        type="password" 
                        id="confirmPassword" 
                        v-model="passwordForm.confirmPassword" 
                        placeholder="请再次输入新密码"
                        required
                        minlength="6"
                      />
                    </div>
                    <button type="submit" class="btn-primary" :disabled="isChangingPassword">
                      <span v-if="!isChangingPassword">修改密码</span>
                      <span v-else>修改中...</span>
                    </button>
                  </form>
                </div>
                
                <div class="setting-section danger-section">
                  <h4>退出登录</h4>
                  <p class="danger-text">退出登录后，您需要重新登录才能访问系统功能。</p>
                  <button @click="logout" class="btn-danger">退出登录</button>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else class="placeholder-content">
            <div class="placeholder-icon">🚧</div>
            <h2>{{ pageTitle }}</h2>
            <p>该功能正在开发中，敬请期待！</p>
          </div>
        </div>
      </main>
    </div>
    
    <div v-else class="auth-container">
      <Login 
        v-if="currentView === 'login'" 
        @switch-to-register="currentView = 'register'"
        @login-success="handleLoginSuccess"
      />
      <Register 
        v-else-if="currentView === 'register'" 
        @switch-to-login="currentView = 'login'"
      />
    </div>
  </div>
</template>

<script>
import Login from './components/Login.vue';
import Register from './components/Register.vue';
import Chat from './components/Chat.vue';
import History from './components/History.vue';
import Sessions from './components/Sessions.vue';
import Evaluations from './components/Evaluations.vue';
import FileUpload from './components/FileUpload.vue';
import RadarChart from './components/RadarChart.vue';
import ProfessionalAssessmentNew from './components/ProfessionalAssessmentNew.vue';

export default {
  name: 'AppApp',
  components: {
    Login,
    Register,
    Chat,
    History,
    Sessions,
    Evaluations,
    FileUpload,
    RadarChart,
    ProfessionalAssessment: ProfessionalAssessmentNew
  },
  data() {
    return {
      currentView: 'login',
      currentPage: 'dashboard',
          isLoggedIn: false,
          username: '',
          latestEvaluation: null,
          isEvaluating: false,
          fileIds: [],
          passwordForm: {
            currentPassword: '',
            newPassword: '',
            confirmPassword: ''
          },
          isChangingPassword: false
    };
  },
  computed: {
    pageTitle() {
      const titles = {
        dashboard: '仪表盘',
        sessions: '会话管理',
        history: '历史记录',
        evaluations: '评分记录',
        files: '文件管理',
        chat: 'AI对话',
        settings: '设置',
        'professional-assessment': '专业测评'
      };
      return titles[this.currentPage] || '仪表盘';
    }
  },
  mounted() {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    if (token && username) {
      this.isLoggedIn = true;
      this.username = username;
      this.loadLatestEvaluation();
    }
  },
  methods: {
    handleLoginSuccess(data) {
      this.isLoggedIn = true;
      this.username = data.username;
      this.loadLatestEvaluation();
    },
    logout() {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      this.isLoggedIn = false;
      this.username = '';
      this.currentView = 'login';
      this.latestEvaluation = null;
    },
    async loadLatestEvaluation() {
      const token = localStorage.getItem('token');
      if (!token) return;

      try {
        const response = await fetch('http://localhost:5000/api/evaluation/latest', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          this.latestEvaluation = data;
        }
      } catch (error) {
        console.error('获取评分失败:', error);
      }
    },
    async startEvaluation() {
      const token = localStorage.getItem('token');
      if (!token) return;

      this.isEvaluating = true;
      try {
        const response = await fetch('http://localhost:5000/api/evaluate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ file_ids: this.fileIds })
        });

        if (response.ok) {
          const data = await response.json();
          this.latestEvaluation = data;
          alert('评分完成！');
        } else {
          const error = await response.json();
          alert('评分失败：' + (error.error || '未知错误'));
        }
      } catch (error) {
        console.error('评分失败:', error);
        alert('评分失败，请稍后重试');
      } finally {
        this.isEvaluating = false;
      }
    },
    handleUseFileForEvaluation(fileId) {
      if (!this.fileIds.includes(fileId)) {
        this.fileIds.push(fileId);
        alert('文件已添加到评估列表，正在进行评估...');
        this.startEvaluation();
      } else {
        alert('文件已在评估列表中，正在进行评估...');
        this.startEvaluation();
      }
    },
    clearFileIds() {
      this.fileIds = [];
      alert('已清空评估文件列表');
    },
    async changePassword() {
      if (this.passwordForm.newPassword !== this.passwordForm.confirmPassword) {
        alert('两次输入的新密码不一致');
        return;
      }

      this.isChangingPassword = true;
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('http://localhost:5000/api/change-password', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            current_password: this.passwordForm.currentPassword,
            new_password: this.passwordForm.newPassword
          })
        });

        if (response.ok) {
          alert('密码修改成功！');
          this.passwordForm = {
            currentPassword: '',
            newPassword: '',
            confirmPassword: ''
          };
        } else {
          const error = await response.json();
          alert('密码修改失败：' + (error.error || '未知错误'));
        }
      } catch (error) {
        console.error('密码修改失败:', error);
        alert('密码修改失败，请稍后重试');
      } finally {
        this.isChangingPassword = false;
      }
    },
    getScoreClass(score) {
      if (score >= 90) {
        return 'excellent';
      } else if (score >= 80) {
        return 'good';
      } else if (score >= 60) {
        return 'average';
      } else {
        return 'poor';
      }
    }
  }
};
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica', sans-serif;
  line-height: 1.6;
  color: #1a1a1a;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  min-height: 100vh;
}

.main-layout {
  display: flex;
  min-height: 100vh;
  background: #f0f2f5;
}

.sidebar {
  width: 280px;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  color: white;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  left: 0;
  top: 0;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.15);
  z-index: 100;
}

.sidebar-header {
  padding: 28px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.logo-icon {
  font-size: 32px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.logo-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar-nav {
  flex: 1;
  padding: 24px 16px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  color: #94a3b8;
  text-decoration: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
  margin-bottom: 8px;
  font-weight: 500;
  font-size: 15px;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  transform: translateX(4px);
}

.nav-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.nav-icon {
  font-size: 20px;
}

.nav-text {
  font: inherit;
}

.sidebar-footer {
  padding: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.user-avatar {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.user-details {
  flex: 1;
}

.user-name {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 4px;
  color: white;
}

.user-role {
  font-size: 13px;
  color: #94a3b8;
}

.logout-btn {
  width: 100%;
  padding: 14px;
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.25);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.main-content {
  flex: 1;
  margin-left: 280px;
  display: flex;
  flex-direction: column;
}

.top-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 20px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 50;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.header-title h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.5px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.action-btn {
  width: 44px;
  height: 44px;
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.action-btn:hover {
  background: #f8fafc;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.content-area {
  flex: 1;
  padding: 40px;
  overflow-y: auto;
}

.dashboard-content {
  max-width: 1400px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.stat-card {
  background: white;
  padding: 28px;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  font-size: 40px;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 6px;
  letter-spacing: -1px;
}

.stat-label {
  font-size: 15px;
  color: #64748b;
  font-weight: 500;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 24px;
}

.content-card {
  background: white;
  padding: 28px;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.content-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.content-card h3 {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid rgba(0, 0, 0, 0.06);
  letter-spacing: -0.5px;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  background: #f8fafc;
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.activity-item:hover {
  background: #f1f5f9;
  transform: translateX(4px);
}

.activity-icon {
  font-size: 18px;
}

.activity-text {
  flex: 1;
  font-size: 15px;
  color: #334155;
  font-weight: 500;
}

.activity-time {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
}

.evaluation-details {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.evaluation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.item-label {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
}

.item-score {
  font-size: 18px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 6px;
}

.item-score.excellent {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.item-score.good {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.item-score.average {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.item-score.poor {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.item-feedback {
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
  max-width: 70%;
}

.evaluation-time {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
  text-align: center;
}

.no-evaluation {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.no-evaluation-icon {
  font-size: 64px;
  margin-bottom: 16px;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
}

.no-evaluation p {
  font-size: 16px;
  color: #64748b;
  margin-bottom: 24px;
  font-weight: 500;
}

.evaluate-btn {
  padding: 12px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  letter-spacing: 0.5px;
}

.evaluate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.evaluate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.evaluation-actions {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.reevaluate-btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  letter-spacing: 0.3px;
}

.reevaluate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.reevaluate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.file-ids-list {
  margin-top: 24px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.file-ids-list h4 {
  margin-bottom: 16px;
  color: #1e293b;
  font-size: 1rem;
  font-weight: 600;
}

.file-ids-content {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.file-id-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #e0f2fe;
  color: #0284c7;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  border: 1px solid #bae6fd;
}

.remove-tag-btn {
  background: none;
  border: none;
  color: #0284c7;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s ease;
}

.remove-tag-btn:hover {
  background: rgba(2, 132, 199, 0.1);
}

.clear-btn {
  padding: 8px 16px;
  background: #fef2f2;
  color: #ef4444;
  border: 1px solid #fee2e2;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-left: auto;
}

.clear-btn:hover {
  background: #fee2e2;
}

.settings-content {
  padding: 24px;
  background: #f8fafc;
  min-height: 600px;
}

.settings-container {
  max-width: 600px;
}

.settings-card {
  background: white;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.settings-card h3 {
  margin-bottom: 24px;
  color: #1e293b;
  font-size: 1.5rem;
  font-weight: 700;
}

.setting-item {
  margin-bottom: 24px;
}

.setting-item label {
  display: block;
  margin-bottom: 8px;
  color: #475569;
  font-weight: 600;
  font-size: 14px;
}

.user-info-display {
  padding: 12px 16px;
  background: #f1f5f9;
  border-radius: 8px;
  color: #1e293b;
  font-size: 16px;
  font-weight: 500;
}

.setting-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e2e8f0;
}

.setting-section h4 {
  margin-bottom: 16px;
  color: #1e293b;
  font-size: 1.1rem;
  font-weight: 600;
}

.danger-section {
  margin-top: 40px;
  padding-top: 32px;
  border-top: 2px solid #fee2e2;
}

.danger-section h4 {
  color: #ef4444;
}

.danger-text {
  color: #64748b;
  font-size: 14px;
  margin-bottom: 16px;
  line-height: 1.6;
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  color: #475569;
  font-weight: 600;
  font-size: 14px;
}

.form-group input {
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 15px;
  transition: all 0.2s ease;
  outline: none;
}

.form-group input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.btn-primary {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 8px;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-danger {
  padding: 12px 24px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.files-content {
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  min-height: 600px;
}

.chart-placeholder {
  height: 240px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed #e2e8f0;
}

.chart-placeholder-text {
  color: #64748b;
  font-size: 16px;
  font-weight: 500;
}

.radar-chart-wrapper {
  width: 50%;
  margin: 0 auto;
  height: 400px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background: white;
  padding: 20px;
}

.chat-content {
  height: calc(100vh - 80px);
  padding: 0;
}

.history-content {
  height: calc(100vh - 80px);
  padding: 0;
}

.evaluations-content {
  height: calc(100vh - 80px);
  padding: 0;
}

.placeholder-content {
  text-align: center;
  padding: 80px 20px;
}

.placeholder-icon {
  font-size: 80px;
  margin-bottom: 24px;
  filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.1));
}

.placeholder-content h2 {
  font-size: 32px;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 12px;
  letter-spacing: -1px;
}

.placeholder-content p {
  font-size: 18px;
  color: #64748b;
  font-weight: 500;
}

.auth-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

@media (max-width: 1024px) {
  .sidebar {
    width: 80px;
  }
  
  .logo-text,
  .nav-text,
  .user-details {
    display: none;
  }
  
  .nav-item {
    justify-content: center;
    padding: 14px;
  }
  
  .nav-item.active {
    border-radius: 12px;
  }
  
  .main-content {
    margin-left: 80px;
  }
  
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .sidebar {
    width: 0;
    transform: translateX(-100%);
  }
  
  .main-content {
    margin-left: 0;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .top-header {
    padding: 16px 24px;
  }
  
  .content-area {
    padding: 24px;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .top-header {
    padding: 16px 20px;
  }
  
  .content-area {
    padding: 20px;
  }
  
  .header-title h1 {
    font-size: 20px;
  }
}
</style>

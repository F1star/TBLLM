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
          <a href="#" class="nav-item active" @click.prevent="currentPage = 'dashboard'">
            <span class="nav-icon">🏠</span>
            <span class="nav-text">仪表盘</span>
          </a>
          <a href="#" class="nav-item" @click.prevent="currentPage = 'assessment'">
            <span class="nav-icon">📝</span>
            <span class="nav-text">能力评估</span>
          </a>
          <a href="#" class="nav-item" @click.prevent="currentPage = 'analysis'">
            <span class="nav-icon">📊</span>
            <span class="nav-text">数据分析</span>
          </a>
          <a href="#" class="nav-item" @click.prevent="currentPage = 'history'">
            <span class="nav-icon">📋</span>
            <span class="nav-text">历史记录</span>
          </a>
          <a href="#" class="nav-item" @click.prevent="currentPage = 'chat'">
            <span class="nav-icon">💬</span>
            <span class="nav-text">AI对话</span>
          </a>
          <a href="#" class="nav-item" @click.prevent="currentPage = 'settings'">
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
                  <div class="stat-value">12</div>
                  <div class="stat-label">已完成评估</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">⭐</div>
                <div class="stat-info">
                  <div class="stat-value">85%</div>
                  <div class="stat-label">平均得分</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">📈</div>
                <div class="stat-info">
                  <div class="stat-value">+15%</div>
                  <div class="stat-label">能力提升</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">🎯</div>
                <div class="stat-info">
                  <div class="stat-value">5</div>
                  <div class="stat-label">待完成任务</div>
                </div>
              </div>
            </div>
            
            <div class="content-grid">
              <div class="content-card">
                <h3>最近活动</h3>
                <div class="activity-list">
                  <div class="activity-item">
                    <div class="activity-icon">✅</div>
                    <div class="activity-text">完成了数学能力评估</div>
                    <div class="activity-time">2小时前</div>
                  </div>
                  <div class="activity-item">
                    <div class="activity-icon">📝</div>
                    <div class="activity-text">开始新的语言能力测试</div>
                    <div class="activity-time">昨天</div>
                  </div>
                  <div class="activity-item">
                    <div class="activity-icon">🏆</div>
                    <div class="activity-text">获得了"进步之星"称号</div>
                    <div class="activity-time">3天前</div>
                  </div>
                </div>
              </div>
              
              <div class="content-card">
                <h3>能力雷达图</h3>
                <div class="chart-placeholder">
                  <div class="chart-placeholder-text">图表区域</div>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else-if="currentPage === 'chat'" class="chat-content">
            <Chat />
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

export default {
  name: 'AppApp',
  components: {
    Login,
    Register,
    Chat
  },
  data() {
    return {
      currentView: 'login',
      currentPage: 'dashboard',
      isLoggedIn: false,
      username: ''
    };
  },
  computed: {
    pageTitle() {
      const titles = {
        dashboard: '仪表盘',
        assessment: '能力评估',
        analysis: '数据分析',
        history: '历史记录',
        chat: 'AI对话',
        settings: '设置'
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
    }
  },
  methods: {
    handleLoginSuccess(data) {
      this.isLoggedIn = true;
      this.username = data.username;
    },
    logout() {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      this.isLoggedIn = false;
      this.username = '';
      this.currentView = 'login';
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
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
  line-height: 1.6;
  color: #333;
  background-color: #f5f7fa;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  min-height: 100vh;
}

.main-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 250px;
  background: #2c3e50;
  color: white;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  left: 0;
  top: 0;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #34495e;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
}

.logo-icon {
  font-size: 24px;
}

.sidebar-nav {
  flex: 1;
  padding: 20px 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  color: #bdc3c7;
  text-decoration: none;
  transition: all 0.3s;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: #34495e;
  color: white;
}

.nav-item.active {
  background: #34495e;
  color: white;
  border-left-color: #3498db;
}

.nav-icon {
  font-size: 18px;
}

.nav-text {
  font-size: 14px;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid #34495e;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 15px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: #3498db;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 16px;
}

.user-details {
  flex: 1;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 2px;
}

.user-role {
  font-size: 12px;
  color: #bdc3c7;
}

.logout-btn {
  width: 100%;
  padding: 10px;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.logout-btn:hover {
  background: #c0392b;
}

.main-content {
  flex: 1;
  margin-left: 250px;
  display: flex;
  flex-direction: column;
}

.top-header {
  background: white;
  padding: 15px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ecf0f1;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-title h1 {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.action-btn {
  width: 36px;
  height: 36px;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.action-btn:hover {
  background: #e9ecef;
}

.content-area {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
}

.dashboard-content {
  max-width: 1200px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  font-size: 32px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #7f8c8d;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.content-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.content-card h3 {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ecf0f1;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
}

.activity-icon {
  font-size: 16px;
}

.activity-text {
  flex: 1;
  font-size: 14px;
  color: #2c3e50;
}

.activity-time {
  font-size: 12px;
  color: #7f8c8d;
}

.chart-placeholder {
  height: 200px;
  background: #f8f9fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder-text {
  font-size: 14px;
  color: #7f8c8d;
}

.chat-content {
  height: calc(100vh - 60px);
  padding: 0;
}

.placeholder-content {
  text-align: center;
  padding: 60px 20px;
}

.placeholder-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.placeholder-content h2 {
  font-size: 24px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 10px;
}

.placeholder-content p {
  font-size: 16px;
  color: #7f8c8d;
}

.auth-container {
  min-height: 100vh;
}

@media (max-width: 768px) {
  .sidebar {
    width: 60px;
  }
  
  .logo-text,
  .nav-text,
  .user-details {
    display: none;
  }
  
  .nav-item {
    justify-content: center;
    padding: 15px 10px;
  }
  
  .nav-item.active {
    border-left-color: transparent;
    border-bottom: 3px solid #3498db;
  }
  
  .main-content {
    margin-left: 60px;
  }
  
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .top-header {
    padding: 15px;
  }
  
  .content-area {
    padding: 15px;
  }
}
</style>

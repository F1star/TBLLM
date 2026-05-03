<template>
  <div class="app">
    <!-- Animated background particles -->
    <div class="bg-particles">
      <div v-for="i in 20" :key="i" class="particle" :style="particleStyle(i)"></div>
    </div>
    <div class="grid-overlay"></div>

    <div v-if="isLoggedIn" class="main-layout">
      <!-- Sidebar -->
      <aside class="sidebar">
        <div class="sidebar-glow"></div>
        <div class="sidebar-header">
          <div class="logo">
            <div class="logo-icon">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <rect x="2" y="2" width="28" height="28" rx="8" stroke="url(#logoGrad)" stroke-width="2" fill="rgba(0,229,255,0.05)"/>
                <path d="M16 8L16 24M8 16L24 16" stroke="url(#logoGrad)" stroke-width="2" stroke-linecap="round"/>
                <circle cx="16" cy="16" r="4" fill="url(#logoGrad)" opacity="0.6"/>
                <defs>
                  <linearGradient id="logoGrad" x1="0" y1="0" x2="32" y2="32">
                    <stop offset="0%" stop-color="#00e5ff"/>
                    <stop offset="100%" stop-color="#7c4dff"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div class="logo-text">
              <span class="logo-title">AI 智评</span>
              <span class="logo-sub">综合能力评价系统</span>
            </div>
          </div>
        </div>

        <nav class="sidebar-nav">
          <a
            v-for="item in navItems"
            :key="item.id"
            href="#"
            :class="['nav-item', { active: currentPage === item.id }]"
            @click.prevent="currentPage = item.id"
          >
            <span class="nav-icon" v-html="item.icon"></span>
            <span class="nav-text">{{ item.label }}</span>
            <span v-if="currentPage === item.id" class="nav-indicator"></span>
          </a>
        </nav>

        <div class="sidebar-footer">
          <div class="user-info">
            <div class="user-avatar">{{ username.charAt(0).toUpperCase() }}</div>
            <div class="user-details">
              <div class="user-name">{{ username }}</div>
              <div class="user-role">学员</div>
            </div>
            <div class="user-status"></div>
          </div>
          <button @click="logout" class="logout-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            <span>退出</span>
          </button>
        </div>
      </aside>

      <main class="main-content">
        <header class="top-header">
          <div class="header-left">
            <h1 class="page-title">{{ pageTitle }}</h1>
            <div class="header-divider"></div>
            <span class="page-subtitle">{{ pageSubtitle }}</span>
          </div>
          <div class="header-right">
            <div class="header-time">{{ currentTime }}</div>
          </div>
        </header>

        <div class="content-area">
          <!-- Dashboard -->
          <div v-if="currentPage === 'dashboard'" class="dashboard-content">
            <div class="stats-grid">
              <div v-for="stat in statsData" :key="stat.label" class="stat-card" :style="{ '--accent': stat.color }">
                <div class="stat-icon" v-html="stat.icon"></div>
                <div class="stat-info">
                  <div class="stat-value">{{ stat.value }}</div>
                  <div class="stat-label">{{ stat.label }}</div>
                </div>
                <div class="stat-glow"></div>
              </div>
            </div>

            <div class="content-grid">
              <div class="content-card">
                <div class="card-header">
                  <h3>能力评估</h3>
                  <div class="card-header-line"></div>
                </div>
                <div v-if="latestEvaluation" class="evaluation-details">
                  <div class="evaluation-scores">
                    <div v-for="(item, idx) in scoreItems" :key="idx" class="score-row">
                      <span class="score-label">{{ item.label }}</span>
                      <div class="score-bar-track">
                        <div class="score-bar-fill" :style="{ width: item.score + '%', '--score-color': item.color }"></div>
                      </div>
                      <span class="score-value" :class="getScoreClass(item.score)">{{ item.score }}</span>
                    </div>
                  </div>
                  <div class="evaluation-feedback">
                    <div class="feedback-label">反馈意见</div>
                    <p>{{ latestEvaluation.feedback }}</p>
                  </div>
                  <div class="evaluation-footer">
                    <span class="evaluation-time">评分时间：{{ formatTime(latestEvaluation.timestamp) }}</span>
                    <div class="eval-actions">
                      <label class="deep-toggle" title="使用 ReAct 深度分析所有会话和文件后再评分">
                        <span class="toggle-label">深度思考</span>
                        <input type="checkbox" v-model="deepMode">
                        <span class="toggle-switch"></span>
                      </label>
                      <button @click="startEvaluation" class="btn-glow" :disabled="isEvaluating">
                        <span v-if="!isEvaluating">重新评估</span>
                        <span v-else>评估中...</span>
                      </button>
                    </div>
                  </div>
                </div>
                <div v-else class="no-evaluation">
                  <div class="no-eval-icon">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.3">
                      <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
                    </svg>
                  </div>
                  <p>暂无评分记录</p>
                  <div class="eval-actions" style="justify-content:center;">
                    <label class="deep-toggle" title="使用 ReAct 深度分析所有会话和文件后再评分">
                      <span class="toggle-label">深度思考</span>
                      <input type="checkbox" v-model="deepMode">
                      <span class="toggle-switch"></span>
                    </label>
                    <button @click="startEvaluation" class="btn-glow" :disabled="isEvaluating">
                      <span v-if="!isEvaluating">开始评估</span>
                      <span v-else>评估中...</span>
                    </button>
                  </div>
                </div>
              </div>

              <div class="content-card">
                <div class="card-header">
                  <h3>能力雷达图</h3>
                  <div class="card-header-line"></div>
                </div>
                <div v-if="latestEvaluation" class="radar-wrapper">
                  <RadarChart :evaluation="latestEvaluation" />
                </div>
                <div v-else class="chart-placeholder">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.2">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                  </svg>
                  <span>暂无评分数据</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Chat -->
          <div v-else-if="currentPage === 'chat'" class="page-view"><Chat /></div>
          <div v-else-if="currentPage === 'sessions'" class="page-view"><Sessions /></div>
          <div v-else-if="currentPage === 'history'" class="page-view"><History /></div>

          <!-- Evaluations -->
          <div v-else-if="currentPage === 'evaluations'" class="page-view"><Evaluations /></div>

          <!-- Professional Assessment -->
          <div v-else-if="currentPage === 'professional-assessment'" class="page-view"><ProfessionalAssessment /></div>

          <!-- Files -->
          <div v-else-if="currentPage === 'files'" class="page-view">
            <FileUpload @useForEvaluation="handleUseFileForEvaluation" />
            <div v-if="fileIds.length > 0" class="file-ids-bar">
              <div class="file-ids-header">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <span>当前评估文件</span>
              </div>
              <div class="file-ids-tags">
                <span v-for="id in fileIds" :key="id" class="file-tag">
                  文件 #{{ id }}
                  <button @click="fileIds = fileIds.filter(fid => fid !== id)" class="tag-remove">&times;</button>
                </span>
                <button @click="clearFileIds" class="tag-clear">清空</button>
              </div>
            </div>
          </div>

          <!-- Settings -->
          <div v-else-if="currentPage === 'settings'" class="page-view">
            <div class="settings-container">
              <div class="content-card">
                <div class="card-header">
                  <h3>账户设置</h3>
                  <div class="card-header-line"></div>
                </div>

                <div class="setting-item">
                  <label>用户名</label>
                  <div class="setting-value">{{ username }}</div>
                </div>

                <div class="setting-section">
                  <h4>修改密码</h4>
                  <form @submit.prevent="changePassword" class="password-form">
                    <div class="form-group">
                      <label for="currentPassword">当前密码</label>
                      <input type="password" id="currentPassword" v-model="passwordForm.currentPassword" placeholder="请输入当前密码" required />
                    </div>
                    <div class="form-group">
                      <label for="newPassword">新密码</label>
                      <input type="password" id="newPassword" v-model="passwordForm.newPassword" placeholder="请输入新密码" required minlength="6" />
                    </div>
                    <div class="form-group">
                      <label for="confirmPassword">确认新密码</label>
                      <input type="password" id="confirmPassword" v-model="passwordForm.confirmPassword" placeholder="请再次输入新密码" required minlength="6" />
                    </div>
                    <button type="submit" class="btn-glow" :disabled="isChangingPassword">
                      <span v-if="!isChangingPassword">修改密码</span>
                      <span v-else>修改中...</span>
                    </button>
                  </form>
                </div>

                <div class="setting-section danger-zone">
                  <h4>退出登录</h4>
                  <p>退出登录后需要重新登录才能访问系统功能。</p>
                  <button @click="logout" class="btn-danger">退出登录</button>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="placeholder-content">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3">
              <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>
            </svg>
            <h2>{{ pageTitle }}</h2>
            <p>该功能正在开发中，敬请期待！</p>
          </div>
        </div>
      </main>
    </div>

    <!-- Auth -->
    <div v-else class="auth-container">
      <div class="auth-bg-grid"></div>
      <div class="auth-content">
        <Login v-if="currentView === 'login'" @switch-to-register="currentView = 'register'" @login-success="handleLoginSuccess" />
        <Register v-else-if="currentView === 'register'" @switch-to-login="currentView = 'login'" />
      </div>
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
    Login, Register, Chat, History, Sessions,
    Evaluations, FileUpload, RadarChart,
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
      deepMode: false,
      fileIds: [],
      passwordForm: { currentPassword: '', newPassword: '', confirmPassword: '' },
      isChangingPassword: false,
      currentTime: '',
      timerInterval: null,

      navItems: [
        { id: 'dashboard', label: '仪表盘', icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>' },
        { id: 'sessions', label: '会话管理', icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>' },
        { id: 'evaluations', label: '评分记录', icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>' },
        { id: 'professional-assessment', label: '专业测评', icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>' },
        { id: 'files', label: '文件管理', icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>' },
        { id: 'chat', label: 'AI对话', icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>' },
        { id: 'settings', label: '设置', icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>' }
      ]
    };
  },
  computed: {
    pageTitle() {
      const titles = {
        dashboard: '仪表盘', sessions: '会话管理', history: '历史记录',
        evaluations: '评分记录', files: '文件管理', chat: 'AI对话',
        settings: '设置', 'professional-assessment': '专业测评'
      };
      return titles[this.currentPage] || '仪表盘';
    },
    pageSubtitle() {
      const subs = {
        dashboard: '总览您的学习与能力评估数据',
        sessions: '管理您的对话会话',
        evaluations: '查看所有能力评分记录',
        chat: '与AI助手进行智能对话',
        files: '上传和管理您的文档',
        settings: '管理您的账户设置',
        'professional-assessment': '进行专业能力测评'
      };
      return subs[this.currentPage] || '';
    },
    statsData() {
      const e = this.latestEvaluation;
      return [
        { label: '综合评分', value: e ? e.overall_score : '-', color: '#00e5ff', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20V10M18 20V4M6 20v-4"/></svg>' },
        { label: '逻辑思维', value: e ? e.logic_score : '-', color: '#7c4dff', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5"/></svg>' },
        { label: '创造力', value: e ? e.creativity_score : '-', color: '#00e676', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1-8.313-12.454z"/></svg>' },
        { label: '表达能力', value: e ? e.expression_score : '-', color: '#ffab00', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>' },
        { label: '知识广度', value: e ? e.knowledge_score : '-', color: '#448aff', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>' }
      ];
    },
    scoreItems() {
      const e = this.latestEvaluation;
      if (!e) return [];
      return [
        { label: '逻辑思维', score: e.logic_score, color: '#7c4dff' },
        { label: '创造力', score: e.creativity_score, color: '#00e676' },
        { label: '表达能力', score: e.expression_score, color: '#ffab00' },
        { label: '知识广度', score: e.knowledge_score, color: '#448aff' }
      ];
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
    // 全局401处理：token过期时退出登录
    window.addEventListener('auth-unauthorized', () => {
      this.logout();
    });
    this.updateTime();
    this.timerInterval = setInterval(() => this.updateTime(), 1000);
  },
  beforeUnmount() {
    clearInterval(this.timerInterval);
  },
  methods: {
    updateTime() {
      const now = new Date();
      this.currentTime = now.toLocaleString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    },
    particleStyle(i) {
      const size = 2 + Math.random() * 4;
      return {
        width: size + 'px',
        height: size + 'px',
        left: Math.random() * 100 + '%',
        top: Math.random() * 100 + '%',
        animationDelay: Math.random() * 10 + 's',
        animationDuration: 10 + Math.random() * 20 + 's',
        opacity: 0.2 + Math.random() * 0.5
      };
    },
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
        const res = await fetch('http://localhost:5000/api/evaluation/latest', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) this.latestEvaluation = await res.json();
      } catch (e) { console.error('获取评分失败:', e); }
    },
    async startEvaluation() {
      const token = localStorage.getItem('token');
      if (!token) return;
      this.isEvaluating = true;
      try {
        const res = await fetch('http://localhost:5000/api/evaluate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ file_ids: this.fileIds, deep_mode: this.deepMode })
        });
        if (res.ok) {
          this.latestEvaluation = await res.json();
          alert('评分完成！');
        } else {
          const err = await res.json();
          alert('评分失败：' + (err.error || '未知错误'));
        }
      } catch (e) {
        console.error('评分失败:', e);
        alert('评分失败，请稍后重试');
      } finally { this.isEvaluating = false; }
    },
    handleUseFileForEvaluation(fileId) {
      if (!this.fileIds.includes(fileId)) {
        this.fileIds.push(fileId);
      }
      alert('文件已添加到评估列表，开始评估...');
      this.startEvaluation();
    },
    clearFileIds() { this.fileIds = []; alert('已清空评估文件列表'); },
    async changePassword() {
      if (this.passwordForm.newPassword !== this.passwordForm.confirmPassword) {
        alert('两次输入的新密码不一致'); return;
      }
      this.isChangingPassword = true;
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('http://localhost:5000/api/change-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ current_password: this.passwordForm.currentPassword, new_password: this.passwordForm.newPassword })
        });
        if (res.ok) {
          alert('密码修改成功！');
          this.passwordForm = { currentPassword: '', newPassword: '', confirmPassword: '' };
        } else {
          const err = await res.json();
          alert('密码修改失败：' + (err.error || '未知错误'));
        }
      } catch (e) { console.error('密码修改失败:', e); alert('密码修改失败，请稍后重试'); }
      finally { this.isChangingPassword = false; }
    },
    getScoreClass(score) {
      if (score >= 90) return 'excellent';
      if (score >= 80) return 'good';
      if (score >= 60) return 'average';
      return 'poor';
    },
    formatTime(ts) {
      if (!ts) return '-';
      return new Date(ts).toLocaleString('zh-CN');
    }
  }
};
</script>

<style>
/* ============ GLOBAL STYLES ============ */
:root {
  --bg-primary: #070b14;
  --bg-secondary: #0d1421;
  --bg-card: rgba(255,255,255,0.03);
  --bg-card-hover: rgba(255,255,255,0.06);
  --border-color: rgba(255,255,255,0.08);
  --border-glow: rgba(0,229,255,0.2);
  --text-primary: #e8eaed;
  --text-secondary: #8892a4;
  --text-muted: #5a6275;
  --accent-cyan: #00e5ff;
  --accent-purple: #7c4dff;
  --accent-green: #00e676;
  --accent-red: #ff1744;
  --accent-orange: #ffab00;
  --accent-blue: #448aff;
  --glow-cyan: 0 0 20px rgba(0,229,255,0.12);
  --glow-purple: 0 0 20px rgba(124,77,255,0.12);
  --font-display: 'Orbitron', 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
  --font-body: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', 'JetBrains Mono', sans-serif;
  --sidebar-width: 260px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-body);
  background: var(--bg-primary);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

/* Animated background */
.bg-particles {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.particle {
  position: absolute;
  background: var(--accent-cyan);
  border-radius: 50%;
  animation: floatParticle linear infinite;
}

@keyframes floatParticle {
  0% { transform: translateY(0) translateX(0) scale(1); opacity: 0; }
  10% { opacity: 0.4; }
  90% { opacity: 0.4; }
  100% { transform: translateY(-100vh) translateX(100px) scale(0); opacity: 0; }
}

.grid-overlay {
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  pointer-events: none;
  z-index: 0;
}

/* ============ AUTH CONTAINER ============ */
.auth-container {
  min-height: 100vh;
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0,229,255,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,229,255,0.05) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 70%);
}

.auth-content {
  position: relative;
  z-index: 2;
  width: 100%;
  display: flex;
  justify-content: center;
}

/* ============ MAIN LAYOUT ============ */
.main-layout {
  display: flex;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

/* ============ SIDEBAR ============ */
.sidebar {
  width: var(--sidebar-width);
  position: fixed;
  height: 100vh;
  left: 0;
  top: 0;
  background: rgba(13, 20, 33, 0.85);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow: hidden;
}

.sidebar-glow {
  position: absolute;
  right: -1px;
  top: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(180deg, transparent, var(--accent-cyan), var(--accent-purple), transparent);
  opacity: 0.5;
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid var(--border-color);
}

.logo {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-icon {
  flex-shrink: 0;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 2px;
}

.logo-sub {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 400;
  letter-spacing: 1px;
  margin-top: 2px;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: 10px;
  margin-bottom: 4px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
  letter-spacing: 0.5px;
}

.nav-item:hover {
  background: rgba(255,255,255,0.05);
  color: var(--text-primary);
}

.nav-item.active {
  background: rgba(0,229,255,0.08);
  color: var(--accent-cyan);
  box-shadow: inset 0 0 20px rgba(0,229,255,0.05);
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
}

.nav-item.active .nav-icon {
  filter: drop-shadow(0 0 6px rgba(0,229,255,0.5));
}

.nav-indicator {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--accent-cyan);
  border-radius: 3px 0 0 3px;
  box-shadow: 0 0 10px rgba(0,229,255,0.5);
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(255,255,255,0.03);
  border-radius: 10px;
  margin-bottom: 12px;
  position: relative;
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  color: #fff;
  box-shadow: 0 0 12px rgba(0,229,255,0.2);
}

.user-details { flex: 1; }

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.user-role {
  font-size: 11px;
  color: var(--text-muted);
}

.user-status {
  width: 8px;
  height: 8px;
  background: var(--accent-green);
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(0,230,118,0.5);
}

.logout-btn {
  width: 100%;
  padding: 10px;
  background: rgba(255,23,68,0.08);
  color: var(--accent-red);
  border: 1px solid rgba(255,23,68,0.15);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: var(--font-body);
}

.logout-btn:hover {
  background: rgba(255,23,68,0.15);
  box-shadow: 0 0 16px rgba(255,23,68,0.15);
}

/* ============ MAIN CONTENT ============ */
.main-content {
  flex: 1;
  margin-left: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.top-header {
  padding: 20px 36px;
  background: rgba(7,11,20,0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-left { display: flex; align-items: center; gap: 16px; }

.page-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 1px;
}

.header-divider {
  width: 1px;
  height: 20px;
  background: var(--border-color);
}

.page-subtitle {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 400;
}

.header-right { display: flex; align-items: center; }

.header-time {
  font-family: var(--font-display);
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 2px;
  padding: 6px 14px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: rgba(0,229,255,0.03);
}

/* ============ CONTENT AREA ============ */
.content-area {
  flex: 1;
  padding: 32px 36px;
  overflow-y: auto;
  min-height: 0;
}

.page-view {
  height: 100%;
  min-height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
}

.page-view > * {
  flex: 1;
  min-height: 0;
}

/* ============ DASHBOARD ============ */
.dashboard-content {
  max-width: 1400px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.4s ease;
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--accent-cyan);
  transform: translateY(-4px);
  box-shadow: var(--glow-cyan);
}

.stat-glow {
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, var(--accent), transparent 70%);
  opacity: 0.05;
  pointer-events: none;
}

.stat-card:hover .stat-glow {
  opacity: 0.1;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(0,229,255,0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  flex-shrink: 0;
}

.stat-info { flex: 1; }

.stat-value {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 2px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
  letter-spacing: 0.5px;
}

/* ============ CONTENT CARDS ============ */
.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 24px;
}

.content-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 28px;
  transition: all 0.3s ease;
}

.content-card:hover {
  border-color: rgba(0,229,255,0.15);
  box-shadow: 0 0 30px rgba(0,229,255,0.04);
}

.card-header {
  margin-bottom: 24px;
}

.card-header h3 {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 1px;
  text-transform: uppercase;
}

.card-header-line {
  width: 40px;
  height: 2px;
  background: linear-gradient(90deg, var(--accent-cyan), transparent);
  margin-top: 8px;
  border-radius: 2px;
}

/* Score rows */
.evaluation-scores { display: flex; flex-direction: column; gap: 14px; margin-bottom: 20px; }

.score-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-label {
  font-size: 12px;
  color: var(--text-secondary);
  width: 70px;
  flex-shrink: 0;
}

.score-bar-track {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,0.06);
  border-radius: 3px;
  overflow: hidden;
}

.score-bar-fill {
  height: 100%;
  border-radius: 3px;
  background: var(--score-color, var(--accent-cyan));
  transition: width 1s ease;
  box-shadow: 0 0 8px var(--score-color, var(--accent-cyan));
}

.score-value {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  width: 40px;
  text-align: right;
}

.evaluation-feedback {
  background: rgba(255,255,255,0.03);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
}

.feedback-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.evaluation-feedback p {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.evaluation-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.evaluation-time {
  font-size: 11px;
  color: var(--text-muted);
}

.no-evaluation {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  text-align: center;
  gap: 16px;
}

.no-eval-icon {
  color: var(--text-muted);
}

.no-evaluation p {
  font-size: 14px;
  color: var(--text-muted);
}

.radar-wrapper {
  width: 100%;
  height: 340px;
}

.chart-placeholder {
  height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--text-muted);
  font-size: 14px;
  border: 1px dashed var(--border-color);
  border-radius: 12px;
}

/* Buttons */
.btn-glow {
  padding: 10px 24px;
  background: linear-gradient(135deg, rgba(0,229,255,0.15), rgba(124,77,255,0.15));
  color: var(--accent-cyan);
  border: 1px solid rgba(0,229,255,0.25);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  font-family: var(--font-body);
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 0.5px;
}

.btn-glow:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(0,229,255,0.25), rgba(124,77,255,0.25));
  box-shadow: var(--glow-cyan);
  transform: translateY(-2px);
}

.btn-glow:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.eval-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.deep-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  font-size: 12px;
  color: var(--text-muted);
  transition: color 0.2s;
}

.deep-toggle:hover {
  color: var(--text-secondary);
}

.deep-toggle input {
  display: none;
}

.toggle-switch {
  position: relative;
  width: 36px;
  height: 20px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px;
  transition: all 0.3s ease;
}

.toggle-switch::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  background: var(--text-muted);
  border-radius: 50%;
  transition: all 0.3s ease;
}

.deep-toggle input:checked + .toggle-switch {
  background: rgba(124,77,255,0.2);
  border-color: rgba(124,77,255,0.4);
  box-shadow: 0 0 12px rgba(124,77,255,0.15);
}

.deep-toggle input:checked + .toggle-switch::after {
  left: 18px;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
}

.btn-danger {
  padding: 10px 24px;
  background: rgba(255,23,68,0.12);
  color: var(--accent-red);
  border: 1px solid rgba(255,23,68,0.2);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  font-family: var(--font-body);
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-danger:hover {
  background: rgba(255,23,68,0.2);
  box-shadow: 0 0 16px rgba(255,23,68,0.15);
}

/* ============ SETTINGS ============ */
.settings-container {
  max-width: 600px;
}

.setting-item {
  margin-bottom: 24px;
}

.setting-item label {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.setting-value {
  padding: 12px 16px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-primary);
}

.setting-section {
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.setting-section h4 {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.5px;
  margin-bottom: 16px;
}

.danger-zone h4 { color: var(--accent-red); }
.danger-zone p {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 16px;
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-group input {
  padding: 12px 16px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 13px;
  outline: none;
  transition: all 0.3s ease;
}

.form-group input:focus {
  border-color: var(--accent-cyan);
  box-shadow: 0 0 16px rgba(0,229,255,0.08);
}

.form-group input::placeholder {
  color: var(--text-muted);
}

/* File IDs bar */
.file-ids-bar {
  margin-top: 20px;
  padding: 16px 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
}

.file-ids-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.file-ids-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.file-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(0,229,255,0.08);
  color: var(--accent-cyan);
  border: 1px solid rgba(0,229,255,0.15);
  border-radius: 6px;
  font-size: 12px;
}

.tag-remove {
  background: none;
  border: none;
  color: var(--accent-cyan);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  opacity: 0.6;
}

.tag-remove:hover { opacity: 1; }

.tag-clear {
  padding: 6px 14px;
  background: rgba(255,23,68,0.08);
  color: var(--accent-red);
  border: 1px solid rgba(255,23,68,0.15);
  border-radius: 6px;
  font-size: 11px;
  cursor: pointer;
  font-family: var(--font-body);
  transition: all 0.2s;
}

.tag-clear:hover {
  background: rgba(255,23,68,0.15);
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  gap: 16px;
  color: var(--text-muted);
}

.placeholder-content h2 {
  font-family: var(--font-display);
  font-size: 20px;
  letter-spacing: 1px;
}

.placeholder-content p {
  font-size: 13px;
}

/* Score colors */
.score-value.excellent { color: var(--accent-green); }
.score-value.good { color: var(--accent-cyan); }
.score-value.average { color: var(--accent-orange); }
.score-value.poor { color: var(--accent-red); }

/* Custom scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(0,229,255,0.15);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(0,229,255,0.25); }

.content-area::-webkit-scrollbar { width: 6px; }
.content-area::-webkit-scrollbar-thumb { background: rgba(0,229,255,0.12); border-radius: 3px; }

/* ============ RESPONSIVE ============ */
@media (max-width: 1024px) {
  :root { --sidebar-width: 72px; }
  .logo-text, .user-details, .nav-text, .user-status, .logout-btn span { display: none; }
  .nav-item { justify-content: center; padding: 14px; }
  .sidebar-footer { padding: 12px; }
  .user-info { justify-content: center; padding: 8px; margin-bottom: 8px; }
  .logout-btn { justify-content: center; padding: 10px; }
  .header-divider, .page-subtitle { display: none; }
  .content-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  :root { --sidebar-width: 0; }
  .sidebar { transform: translateX(-100%); width: 0; border: none; }
  .main-content { margin-left: 0; }
  .top-header { padding: 16px 20px; }
  .content-area { padding: 20px; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .page-title { font-size: 16px; }
}

@media (max-width: 480px) {
  .stats-grid { grid-template-columns: 1fr; }
  .content-area { padding: 16px; }
}
</style>

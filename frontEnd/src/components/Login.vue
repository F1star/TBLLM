<template>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="card-glow"></div>

      <div class="login-header">
        <div class="login-logo">
          <svg width="48" height="48" viewBox="0 0 32 32" fill="none">
            <rect x="2" y="2" width="28" height="28" rx="8" stroke="url(#loginGrad)" stroke-width="1.5" fill="rgba(0,229,255,0.03)"/>
            <path d="M16 8L16 24M8 16L24 16" stroke="url(#loginGrad)" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="16" cy="16" r="3" fill="url(#loginGrad)" opacity="0.4"/>
            <defs>
              <linearGradient id="loginGrad" x1="0" y1="0" x2="32" y2="32">
                <stop offset="0%" stop-color="#00e5ff"/>
                <stop offset="100%" stop-color="#7c4dff"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 class="login-title">AI 智评</h1>
        <p class="login-subtitle">登录您的账户以继续</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="email">邮箱地址</label>
          <div class="input-wrap">
            <svg class="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
            <input type="email" id="email" v-model="form.email" placeholder="请输入您的邮箱" required />
          </div>
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <div class="input-wrap">
            <svg class="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            <input type="password" id="password" v-model="form.password" placeholder="请输入您的密码" required />
          </div>
        </div>

        <div class="form-options">
          <label class="checkbox-label">
            <input type="checkbox" checked />
            <span>记住我</span>
          </label>
          <a href="#" class="forgot-link">忘记密码？</a>
        </div>

        <button type="submit" class="login-btn" :disabled="loading">
          <span v-if="!loading">登录</span>
          <span v-else class="loading-text">登录中<span class="dots"><span>.</span><span>.</span><span>.</span></span></span>
        </button>
      </form>

      <div class="login-footer">
        <p>还没有账号？<a href="#" @click.prevent="$emit('switch-to-register')">立即注册</a></p>
      </div>

      <div v-if="error" class="error-msg">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Login',
  emits: ['switch-to-register', 'login-success'],
  data() {
    return {
      form: { email: '', password: '' },
      error: '',
      loading: false
    };
  },
  methods: {
    async handleLogin() {
      try {
        this.error = '';
        this.loading = true;
        const response = await axios.post('http://localhost:5000/api/login', this.form);
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('username', response.data.username);
        this.$emit('login-success', response.data);
      } catch (error) {
        this.error = error.response?.data?.message || '登录失败，请检查网络连接';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.login-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  width: 100%;
}

.login-card {
  background: rgba(13, 20, 33, 0.7);
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
  border: 1px solid rgba(0,229,255,0.12);
  border-radius: 24px;
  padding: 48px;
  width: 100%;
  max-width: 420px;
  position: relative;
  overflow: hidden;
  animation: cardEnter 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes cardEnter {
  from { opacity: 0; transform: translateY(30px) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.card-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 30% 20%, rgba(0,229,255,0.04) 0%, transparent 50%),
              radial-gradient(circle at 70% 80%, rgba(124,77,255,0.04) 0%, transparent 50%);
  pointer-events: none;
  animation: glowRotate 20s linear infinite;
}

@keyframes glowRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
  position: relative;
  z-index: 1;
}

.login-logo {
  margin-bottom: 20px;
  filter: drop-shadow(0 0 20px rgba(0,229,255,0.2));
}

.login-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: #e8eaed;
  letter-spacing: 4px;
  margin-bottom: 8px;
}

.login-subtitle {
  font-size: 13px;
  color: #5a6275;
  font-weight: 400;
  letter-spacing: 0.5px;
}

.login-form {
  position: relative;
  z-index: 1;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 11px;
  color: #5a6275;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
  font-weight: 500;
}

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 14px;
  color: #5a6275;
  pointer-events: none;
  z-index: 1;
}

.form-group input {
  width: 100%;
  padding: 14px 14px 14px 42px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: #e8eaed;
  transition: all 0.3s ease;
  outline: none;
}

.form-group input:focus {
  border-color: rgba(0,229,255,0.4);
  background: rgba(0,229,255,0.03);
  box-shadow: 0 0 24px rgba(0,229,255,0.06);
}

.form-group input::placeholder {
  color: #3a4258;
  font-size: 12px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #5a6275;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #00e5ff;
  cursor: pointer;
}

.forgot-link {
  font-size: 12px;
  color: #5a6275;
  text-decoration: none;
  transition: color 0.3s;
}

.forgot-link:hover {
  color: #00e5ff;
}

.login-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, rgba(0,229,255,0.15), rgba(124,77,255,0.15));
  color: #00e5ff;
  border: 1px solid rgba(0,229,255,0.25);
  border-radius: 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 2px;
  position: relative;
  overflow: hidden;
}

.login-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(0,229,255,0.25), rgba(124,77,255,0.25));
  box-shadow: 0 0 30px rgba(0,229,255,0.15);
  transform: translateY(-2px);
}

.login-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-text { display: inline-flex; align-items: center; gap: 2px; }
.dots span { animation: dotPulse 1.4s infinite; }
.dots span:nth-child(2) { animation-delay: 0.2s; }
.dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotPulse { 0%, 80%, 100% { opacity: 0; } 40% { opacity: 1; } }

.login-footer {
  text-align: center;
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid rgba(255,255,255,0.06);
  position: relative;
  z-index: 1;
}

.login-footer p {
  font-size: 12px;
  color: #5a6275;
}

.login-footer a {
  color: #00e5ff;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s;
}

.login-footer a:hover {
  text-shadow: 0 0 12px rgba(0,229,255,0.4);
}

.error-msg {
  margin-top: 20px;
  padding: 12px 16px;
  background: rgba(255,23,68,0.08);
  border: 1px solid rgba(255,23,68,0.15);
  border-radius: 8px;
  color: #ff1744;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
  z-index: 1;
  animation: shake 0.4s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

@media (max-width: 480px) {
  .login-card { padding: 36px 24px; border-radius: 20px; }
  .login-title { font-size: 20px; }
  .login-logo svg { width: 40px; height: 40px; }
}
</style>

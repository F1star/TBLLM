<template>
  <div class="register-wrapper">
    <div class="register-card">
      <div class="card-glow"></div>

      <div class="register-header">
        <div class="register-logo">
          <svg width="48" height="48" viewBox="0 0 32 32" fill="none">
            <rect x="2" y="2" width="28" height="28" rx="8" stroke="url(#regGrad)" stroke-width="1.5" fill="rgba(0,229,255,0.03)"/>
            <path d="M16 8L16 24M8 16L24 16" stroke="url(#regGrad)" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="16" cy="16" r="3" fill="url(#regGrad)" opacity="0.4"/>
            <path d="M12 20h8M14 16h4" stroke="url(#regGrad)" stroke-width="1.5" stroke-linecap="round"/>
            <defs>
              <linearGradient id="regGrad" x1="0" y1="0" x2="32" y2="32">
                <stop offset="0%" stop-color="#7c4dff"/>
                <stop offset="100%" stop-color="#00e5ff"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 class="register-title">创建账户</h1>
        <p class="register-subtitle">开始您的学习之旅</p>
      </div>

      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <div class="input-wrap">
            <svg class="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            <input type="text" id="username" v-model="form.username" placeholder="请输入用户名" required />
          </div>
        </div>

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
            <input type="password" id="password" v-model="form.password" placeholder="请设置密码" required />
          </div>
        </div>

        <div class="form-group">
          <label for="confirm-password">确认密码</label>
          <div class="input-wrap">
            <svg class="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              <circle cx="12" cy="16" r="1"/>
            </svg>
            <input type="password" id="confirm-password" v-model="form.confirmPassword" placeholder="请再次输入密码" required />
          </div>
        </div>

        <div class="form-options">
          <label class="checkbox-label">
            <input type="checkbox" required />
            <span>我已阅读并同意服务条款和隐私政策</span>
          </label>
        </div>

        <button type="submit" class="register-btn" :disabled="loading">
          <span v-if="!loading">注册</span>
          <span v-else class="loading-text">注册中<span class="dots"><span>.</span><span>.</span><span>.</span></span></span>
        </button>
      </form>

      <div class="register-footer">
        <p>已有账号？<a href="#" @click.prevent="$emit('switch-to-login')">立即登录</a></p>
      </div>

      <div v-if="error" class="error-msg">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        {{ error }}
      </div>
      <div v-if="success" class="success-msg">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        {{ success }}
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Register',
  emits: ['switch-to-login'],
  data() {
    return {
      form: { username: '', email: '', password: '', confirmPassword: '' },
      error: '', success: '', loading: false
    };
  },
  methods: {
    async handleRegister() {
      try {
        this.error = '';
        this.success = '';
        if (this.form.password !== this.form.confirmPassword) {
          this.error = '两次输入的密码不一致';
          return;
        }
        this.loading = true;
        const response = await axios.post('http://localhost:5000/api/register', {
          username: this.form.username, email: this.form.email, password: this.form.password
        });
        this.success = response.data.message;
        this.form = { username: '', email: '', password: '', confirmPassword: '' };
        setTimeout(() => this.$emit('switch-to-login'), 2000);
      } catch (error) {
        this.error = error.response?.data?.message || '注册失败，请检查网络连接';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.register-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  width: 100%;
}

.register-card {
  background: rgba(13, 20, 33, 0.7);
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
  border: 1px solid rgba(124,77,255,0.12);
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
  background: radial-gradient(circle at 70% 20%, rgba(124,77,255,0.04) 0%, transparent 50%),
              radial-gradient(circle at 30% 80%, rgba(0,229,255,0.04) 0%, transparent 50%);
  pointer-events: none;
  animation: glowRotate 20s linear infinite;
}

@keyframes glowRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.register-header {
  text-align: center;
  margin-bottom: 36px;
  position: relative;
  z-index: 1;
}

.register-logo {
  margin-bottom: 20px;
  filter: drop-shadow(0 0 20px rgba(124,77,255,0.2));
}

.register-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: #e8eaed;
  letter-spacing: 4px;
  margin-bottom: 8px;
}

.register-subtitle {
  font-size: 13px;
  color: #5a6275;
  letter-spacing: 0.5px;
}

.register-form { position: relative; z-index: 1; }

.form-group { margin-bottom: 20px; }

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
  border-color: rgba(124,77,255,0.4);
  background: rgba(124,77,255,0.03);
  box-shadow: 0 0 24px rgba(124,77,255,0.06);
}

.form-group input::placeholder { color: #3a4258; font-size: 12px; }

.form-options { margin-bottom: 28px; }

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 12px;
  color: #5a6275;
  cursor: pointer;
  line-height: 1.5;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #7c4dff;
  cursor: pointer;
  margin-top: 2px;
}

.register-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, rgba(124,77,255,0.15), rgba(0,229,255,0.15));
  color: #7c4dff;
  border: 1px solid rgba(124,77,255,0.25);
  border-radius: 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 2px;
}

.register-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(124,77,255,0.25), rgba(0,229,255,0.25));
  box-shadow: 0 0 30px rgba(124,77,255,0.15);
  transform: translateY(-2px);
}

.register-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.loading-text { display: inline-flex; align-items: center; gap: 2px; }
.dots span { animation: dotPulse 1.4s infinite; }
.dots span:nth-child(2) { animation-delay: 0.2s; }
.dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotPulse { 0%, 80%, 100% { opacity: 0; } 40% { opacity: 1; } }

.register-footer {
  text-align: center;
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid rgba(255,255,255,0.06);
  position: relative;
  z-index: 1;
}

.register-footer p { font-size: 12px; color: #5a6275; }

.register-footer a {
  color: #7c4dff;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s;
}

.register-footer a:hover {
  text-shadow: 0 0 12px rgba(124,77,255,0.4);
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

.success-msg {
  margin-top: 20px;
  padding: 12px 16px;
  background: rgba(0,230,118,0.08);
  border: 1px solid rgba(0,230,118,0.15);
  border-radius: 8px;
  color: #00e676;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
  z-index: 1;
  animation: fadeIn 0.5s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 480px) {
  .register-card { padding: 36px 24px; border-radius: 20px; }
  .register-title { font-size: 20px; }
  .register-logo svg { width: 40px; height: 40px; }
}
</style>

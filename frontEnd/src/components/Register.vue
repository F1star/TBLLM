<template>
  <div class="register-container">
    <div class="register-box">
      <div class="register-header">
        <div class="logo-icon">📊</div>
        <h1>青少年综合能力评价系统</h1>
        <p>创建账户，开始您的学习之旅</p>
      </div>
      
      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <div class="input-wrapper">
            <span class="input-icon">👤</span>
            <input 
              type="text" 
              id="username" 
              v-model="form.username" 
              placeholder="请输入用户名"
              required
            >
          </div>
        </div>
        
        <div class="form-group">
          <label for="email">邮箱地址</label>
          <div class="input-wrapper">
            <span class="input-icon">📧</span>
            <input 
              type="email" 
              id="email" 
              v-model="form.email" 
              placeholder="请输入您的邮箱"
              required
            >
          </div>
        </div>
        
        <div class="form-group">
          <label for="password">密码</label>
          <div class="input-wrapper">
            <span class="input-icon">🔒</span>
            <input 
              type="password" 
              id="password" 
              v-model="form.password" 
              placeholder="请设置您的密码"
              required
            >
          </div>
        </div>
        
        <div class="form-group">
          <label for="confirm-password">确认密码</label>
          <div class="input-wrapper">
            <span class="input-icon">🔐</span>
            <input 
              type="password" 
              id="confirm-password" 
              v-model="form.confirmPassword" 
              placeholder="请再次输入密码"
              required
            >
          </div>
        </div>
        
        <div class="form-options">
          <label class="checkbox-label">
            <input type="checkbox" required>
            <span>我已阅读并同意服务条款和隐私政策</span>
          </label>
        </div>
        
        <button type="submit" class="register-btn" :disabled="loading">
          <span v-if="!loading">注册</span>
          <span v-else>注册中...</span>
        </button>
      </form>
      
      <div class="register-footer">
        <p>已有账号？<a href="#" @click.prevent="$emit('switch-to-login')">立即登录</a></p>
      </div>
      
      <div v-if="error" class="error-message">
        <span class="error-icon">⚠️</span>
        {{ error }}
      </div>
      <div v-if="success" class="success-message">
        <span class="success-icon">✅</span>
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
      form: {
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
      },
      error: '',
      success: '',
      loading: false
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
          username: this.form.username,
          email: this.form.email,
          password: this.form.password
        });
        this.success = response.data.message;
        this.form = {
          username: '',
          email: '',
          password: '',
          confirmPassword: ''
        };
        setTimeout(() => {
          this.$emit('switch-to-login');
        }, 2000);
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
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.register-container::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
  animation: rotate 30s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.register-box {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 48px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
  z-index: 1;
  animation: slideUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.register-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo-icon {
  font-size: 64px;
  margin-bottom: 16px;
  filter: drop-shadow(0 4px 12px rgba(102, 126, 234, 0.4));
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.register-header h1 {
  font-size: 28px;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 12px;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.register-header p {
  font-size: 16px;
  color: #64748b;
  font-weight: 500;
}

.register-form {
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  margin-bottom: 10px;
  font-weight: 600;
  font-size: 15px;
  color: #1e293b;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 16px;
  font-size: 18px;
  color: #94a3b8;
  z-index: 1;
}

.form-group input {
  width: 100%;
  padding: 16px 16px 16px 48px;
  border: 2px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  font-size: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: #f8fafc;
  color: #1e293b;
  font-weight: 500;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.form-group input::placeholder {
  color: #94a3b8;
}

.form-options {
  margin-bottom: 28px;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 14px;
  color: #64748b;
  cursor: pointer;
  font-weight: 500;
  line-height: 1.5;
}

.checkbox-label input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  margin-top: 2px;
  accent-color: #667eea;
}

.register-btn {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
  letter-spacing: 0.5px;
}

.register-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.5);
}

.register-btn:active:not(:disabled) {
  transform: translateY(0);
}

.register-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.register-footer {
  text-align: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.register-footer p {
  font-size: 15px;
  color: #64748b;
  font-weight: 500;
}

.register-footer a {
  color: #667eea;
  text-decoration: none;
  font-weight: 700;
  transition: all 0.3s;
}

.register-footer a:hover {
  color: #764ba2;
  text-decoration: underline;
}

.error-message {
  margin-top: 24px;
  padding: 16px;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 2px solid rgba(239, 68, 68, 0.2);
  border-radius: 12px;
  font-size: 15px;
  text-align: center;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  animation: shake 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-5px);
  }
  75% {
    transform: translateX(5px);
  }
}

.error-icon {
  font-size: 18px;
}

.success-message {
  margin-top: 24px;
  padding: 16px;
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border: 2px solid rgba(16, 185, 129, 0.2);
  border-radius: 12px;
  font-size: 15px;
  text-align: center;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  animation: slideIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.success-icon {
  font-size: 18px;
}

@media (max-width: 480px) {
  .register-box {
    padding: 36px 24px;
    border-radius: 20px;
  }
  
  .register-header h1 {
    font-size: 24px;
  }
  
  .logo-icon {
    font-size: 48px;
  }
  
  .form-group input {
    padding: 14px 14px 14px 44px;
    font-size: 15px;
  }
  
  .register-btn {
    padding: 14px;
    font-size: 16px;
  }
}
</style>

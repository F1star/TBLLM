<template>
  <div class="register-container">
    <div class="register-box">
      <div class="register-header">
        <h1>青少年综合能力评价系统</h1>
        <p>创建账户，开始您的学习之旅</p>
      </div>
      
      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input 
            type="text" 
            id="username" 
            v-model="form.username" 
            placeholder="请输入用户名"
            required
          >
        </div>
        
        <div class="form-group">
          <label for="email">邮箱地址</label>
          <input 
            type="email" 
            id="email" 
            v-model="form.email" 
            placeholder="请输入您的邮箱"
            required
          >
        </div>
        
        <div class="form-group">
          <label for="password">密码</label>
          <input 
            type="password" 
            id="password" 
            v-model="form.password" 
            placeholder="请设置您的密码"
            required
          >
        </div>
        
        <div class="form-group">
          <label for="confirm-password">确认密码</label>
          <input 
            type="password" 
            id="confirm-password" 
            v-model="form.confirmPassword" 
            placeholder="请再次输入密码"
            required
          >
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
      
      <div v-if="error" class="error-message">{{ error }}</div>
      <div v-if="success" class="success-message">{{ success }}</div>
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
  background: #f5f7fa;
  padding: 20px;
}

.register-box {
  background: white;
  border-radius: 8px;
  padding: 40px;
  width: 100%;
  max-width: 450px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.register-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 10px;
}

.register-header p {
  font-size: 14px;
  color: #7f8c8d;
}

.register-form {
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  font-size: 14px;
  color: #2c3e50;
}

.form-group input {
  width: 100%;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
}

.form-group input::placeholder {
  color: #bdc3c7;
}

.form-options {
  margin-bottom: 20px;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 13px;
  color: #7f8c8d;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
  margin-top: 2px;
}

.register-btn {
  width: 100%;
  padding: 12px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.register-btn:hover:not(:disabled) {
  background: #2980b9;
}

.register-btn:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.register-footer {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ecf0f1;
}

.register-footer p {
  font-size: 14px;
  color: #7f8c8d;
}

.register-footer a {
  color: #3498db;
  text-decoration: none;
  font-weight: 500;
}

.register-footer a:hover {
  text-decoration: underline;
}

.error-message {
  margin-top: 20px;
  padding: 12px;
  background: #fee;
  color: #e74c3c;
  border: 1px solid #f5b7b1;
  border-radius: 4px;
  font-size: 14px;
  text-align: center;
}

.success-message {
  margin-top: 20px;
  padding: 12px;
  background: #e8f5e8;
  color: #2e7d32;
  border: 1px solid #a8d5a2;
  border-radius: 4px;
  font-size: 14px;
  text-align: center;
}

@media (max-width: 480px) {
  .register-box {
    padding: 30px 20px;
  }
  
  .register-header h1 {
    font-size: 20px;
  }
}
</style>

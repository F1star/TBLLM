<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>青少年综合能力评价系统</h1>
        <p>登录您的账户以继续</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
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
            placeholder="请输入您的密码"
            required
          >
        </div>
        
        <div class="form-options">
          <label class="checkbox-label">
            <input type="checkbox">
            <span>记住我</span>
          </label>
          <a href="#" class="forgot-link">忘记密码？</a>
        </div>
        
        <button type="submit" class="login-btn" :disabled="loading">
          <span v-if="!loading">登录</span>
          <span v-else>登录中...</span>
        </button>
      </form>
      
      <div class="login-footer">
        <p>还没有账号？<a href="#" @click.prevent="$emit('switch-to-register')">立即注册</a></p>
      </div>
      
      <div v-if="error" class="error-message">{{ error }}</div>
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
      form: {
        email: '',
        password: ''
      },
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
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.login-box {
  background: white;
  border-radius: 8px;
  padding: 40px;
  width: 100%;
  max-width: 450px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 10px;
}

.login-header p {
  font-size: 14px;
  color: #7f8c8d;
}

.login-form {
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #7f8c8d;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
}

.forgot-link {
  font-size: 14px;
  color: #3498db;
  text-decoration: none;
}

.forgot-link:hover {
  text-decoration: underline;
}

.login-btn {
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

.login-btn:hover:not(:disabled) {
  background: #2980b9;
}

.login-btn:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ecf0f1;
}

.login-footer p {
  font-size: 14px;
  color: #7f8c8d;
}

.login-footer a {
  color: #3498db;
  text-decoration: none;
  font-weight: 500;
}

.login-footer a:hover {
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

@media (max-width: 480px) {
  .login-box {
    padding: 30px 20px;
  }
  
  .login-header h1 {
    font-size: 20px;
  }
}
</style>

<template>
  <div class="evaluations-container">
    <div class="evaluations-header">
      <h2>📊 评分记录</h2>
      <div class="header-actions">
        <button @click="loadEvaluations" class="refresh-btn">
          <span>🔄</span>
          <span>刷新</span>
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="evaluations.length === 0" class="empty-state">
      <div class="empty-icon">📊</div>
      <p class="empty-title">暂无评分记录</p>
      <p class="empty-hint">在历史记录中对对话进行评分，记录将显示在这里</p>
    </div>

    <div v-else class="evaluations-list">
      <div v-for="evaluation in evaluations" :key="evaluation.id" class="evaluation-card" @click="viewEvaluation(evaluation)">
        <div class="card-header">
          <div class="card-date">{{ formatDate(evaluation.timestamp) }}</div>
          <div class="card-time">{{ formatTime(evaluation.timestamp) }}</div>
        </div>
        
        <div class="card-body">
          <div class="overall-score">
            <span class="score-label">综合评分</span>
            <span class="score-value" :class="getScoreClass(evaluation.overall_score)">
              {{ evaluation.overall_score }}
            </span>
          </div>
          
          <div class="score-details">
            <div class="score-item">
              <span class="item-label">逻辑思维</span>
              <span class="item-score" :class="getScoreClass(evaluation.logic_score)">
                {{ evaluation.logic_score }}
              </span>
            </div>
            <div class="score-item">
              <span class="item-label">创造力</span>
              <span class="item-score" :class="getScoreClass(evaluation.creativity_score)">
                {{ evaluation.creativity_score }}
              </span>
            </div>
            <div class="score-item">
              <span class="item-label">表达能力</span>
              <span class="item-score" :class="getScoreClass(evaluation.expression_score)">
                {{ evaluation.expression_score }}
              </span>
            </div>
            <div class="score-item">
              <span class="item-label">知识广度</span>
              <span class="item-score" :class="getScoreClass(evaluation.knowledge_score)">
                {{ evaluation.knowledge_score }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedEvaluation" class="evaluation-modal" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>评分详情</h3>
          <button @click="closeModal" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="modal-info">
            <div class="info-item">
              <span class="info-label">评分时间</span>
              <span class="info-value">{{ formatFullTime(selectedEvaluation.timestamp) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">对话ID</span>
              <span class="info-value">{{ selectedEvaluation.chat_history_id }}</span>
            </div>
          </div>

          <div class="evaluation-section">
            <h4>综合评分</h4>
            <div class="overall-score-large" :class="getScoreClass(selectedEvaluation.overall_score)">
              {{ selectedEvaluation.overall_score }}
            </div>
          </div>

          <div class="evaluation-section">
            <h4>分项评分</h4>
            <div class="evaluation-grid">
              <div class="evaluation-item">
                <span class="evaluation-label">逻辑思维</span>
                <span class="evaluation-score" :class="getScoreClass(selectedEvaluation.logic_score)">
                  {{ selectedEvaluation.logic_score }}
                </span>
              </div>
              <div class="evaluation-item">
                <span class="evaluation-label">创造力</span>
                <span class="evaluation-score" :class="getScoreClass(selectedEvaluation.creativity_score)">
                  {{ selectedEvaluation.creativity_score }}
                </span>
              </div>
              <div class="evaluation-item">
                <span class="evaluation-label">表达能力</span>
                <span class="evaluation-score" :class="getScoreClass(selectedEvaluation.expression_score)">
                  {{ selectedEvaluation.expression_score }}
                </span>
              </div>
              <div class="evaluation-item">
                <span class="evaluation-label">知识广度</span>
                <span class="evaluation-score" :class="getScoreClass(selectedEvaluation.knowledge_score)">
                  {{ selectedEvaluation.knowledge_score }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="selectedEvaluation.feedback" class="evaluation-section">
            <h4>反馈意见</h4>
            <p class="feedback-text">{{ selectedEvaluation.feedback }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const evaluations = ref([])
const loading = ref(false)
const selectedEvaluation = ref(null)

const API_URL = 'http://localhost:5000/api/evaluations'

const getToken = () => {
  return localStorage.getItem('token')
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const formatDate = (timestamp) => {
  const date = new Date(timestamp)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  if (date.toDateString() === today.toDateString()) {
    return '今天'
  } else if (date.toDateString() === yesterday.toDateString()) {
    return '昨天'
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })
  }
}

const formatFullTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric',
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const getScoreClass = (score) => {
  if (score >= 90) {
    return 'excellent'
  } else if (score >= 80) {
    return 'good'
  } else if (score >= 60) {
    return 'average'
  } else {
    return 'poor'
  }
}

const loadEvaluations = async () => {
  const token = getToken()
  if (!token) {
    alert('请先登录')
    return
  }

  loading.value = true
  try {
    const response = await fetch(API_URL, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error('获取评分记录失败')
    }

    const data = await response.json()
    evaluations.value = data
  } catch (error) {
    console.error('获取评分记录失败:', error)
    alert('获取评分记录失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const viewEvaluation = (evaluation) => {
  selectedEvaluation.value = evaluation
}

const closeModal = () => {
  selectedEvaluation.value = null
}

onMounted(() => {
  loadEvaluations()
})
</script>

<style scoped>
.evaluations-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0;
}

.evaluations-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  background: white;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.evaluations-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  letter-spacing: -0.5px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.refresh-btn {
  padding: 10px 20px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 6px;
  background: white;
}

.refresh-btn:hover {
  background: #f8fafc;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #64748b;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(102, 126, 234, 0.2);
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #64748b;
  text-align: center;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 24px;
  filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.1));
}

.empty-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #1e293b;
}

.empty-hint {
  font-size: 16px;
  color: #64748b;
}

.evaluations-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
}

.evaluation-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.evaluation-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.card-date {
  font-size: 16px;
  font-weight: 700;
}

.card-time {
  font-size: 14px;
  font-weight: 600;
  opacity: 0.9;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.overall-score {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
}

.score-label {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.score-value {
  font-size: 28px;
  font-weight: 800;
  padding: 8px 16px;
  border-radius: 8px;
}

.score-value.excellent {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.score-value.good {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.score-value.average {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.score-value.poor {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.score-details {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.score-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.item-label {
  font-size: 13px;
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

.evaluation-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 20px;
  max-width: 700px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.close-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: #f8fafc;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  transition: all 0.3s;
}

.close-btn:hover {
  background: #e2e8f0;
  transform: rotate(90deg);
}

.modal-body {
  padding: 28px;
}

.modal-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
}

.info-value {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.evaluation-section {
  margin-bottom: 24px;
}

.evaluation-section h4 {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 16px;
}

.overall-score-large {
  font-size: 64px;
  font-weight: 800;
  padding: 24px;
  background: #f8fafc;
  border-radius: 16px;
  text-align: center;
}

.overall-score-large.excellent {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.overall-score-large.good {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.overall-score-large.average {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.overall-score-large.poor {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.evaluation-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.evaluation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 2px solid rgba(0, 0, 0, 0.05);
}

.evaluation-label {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
}

.evaluation-score {
  font-size: 24px;
  font-weight: 800;
  padding: 8px 16px;
  border-radius: 8px;
}

.evaluation-score.excellent {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.evaluation-score.good {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.evaluation-score.average {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.evaluation-score.poor {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.feedback-text {
  font-size: 15px;
  line-height: 1.8;
  color: #64748b;
  background: #f8fafc;
  padding: 16px;
  border-radius: 12px;
  border-left: 4px solid #667eea;
}

.evaluations-list::-webkit-scrollbar {
  width: 8px;
}

.evaluations-list::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.evaluations-list::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
}

@media (max-width: 768px) {
  .evaluations-header {
    padding: 20px 24px;
  }
  
  .evaluations-header h2 {
    font-size: 20px;
  }
  
  .evaluations-list {
    padding: 20px 24px;
    grid-template-columns: 1fr;
  }
  
  .evaluation-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    max-height: 95vh;
  }
}

@media (max-width: 480px) {
  .evaluations-header {
    padding: 16px 20px;
  }
  
  .evaluations-header h2 {
    font-size: 18px;
  }
  
  .evaluations-list {
    padding: 16px 20px;
  }
  
  .score-details {
    grid-template-columns: 1fr;
  }
}
</style>

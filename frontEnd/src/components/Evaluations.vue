<template>
  <div class="evaluations-container">
    <div class="evaluations-header">
      <h2>评分记录</h2>
      <button @click="loadEvaluations" class="refresh-btn">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        刷新
      </button>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loader"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="evaluations.length === 0" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.2">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
      </svg>
      <p class="empty-title">暂无评分记录</p>
      <p class="empty-hint">在历史记录中对对话进行评分，记录将显示在这里</p>
    </div>

    <div v-else class="evaluations-list">
      <div v-for="evaluation in evaluations" :key="evaluation.id" class="evaluation-card" @click="viewEvaluation(evaluation)">
        <div class="card-accent"></div>
        <div class="card-top">
          <div class="card-date">{{ formatDate(evaluation.timestamp) }}</div>
          <div class="card-time">{{ formatTime(evaluation.timestamp) }}</div>
        </div>

        <div class="card-score-main">
          <span class="score-label">综合评分</span>
          <span class="score-big" :class="getScoreClass(evaluation.overall_score)">{{ evaluation.overall_score }}</span>
        </div>

        <div class="card-scores">
          <div class="card-score-item">
            <span class="cs-label">逻辑</span>
            <span class="cs-value" :class="getScoreClass(evaluation.logic_score)">{{ evaluation.logic_score }}</span>
          </div>
          <div class="card-score-item">
            <span class="cs-label">创造</span>
            <span class="cs-value" :class="getScoreClass(evaluation.creativity_score)">{{ evaluation.creativity_score }}</span>
          </div>
          <div class="card-score-item">
            <span class="cs-label">表达</span>
            <span class="cs-value" :class="getScoreClass(evaluation.expression_score)">{{ evaluation.expression_score }}</span>
          </div>
          <div class="card-score-item">
            <span class="cs-label">知识</span>
            <span class="cs-value" :class="getScoreClass(evaluation.knowledge_score)">{{ evaluation.knowledge_score }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="selectedEvaluation" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>评分详情</h3>
          <button @click="closeModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="modal-info">
            <div class="info-row">
              <span class="info-label">评分时间</span>
              <span class="info-value">{{ formatFullTime(selectedEvaluation.timestamp) }}</span>
            </div>
          </div>

          <div class="detail-section">
            <h4>综合评分</h4>
            <div class="overall-large" :class="getScoreClass(selectedEvaluation.overall_score)">
              {{ selectedEvaluation.overall_score }}
            </div>
          </div>

          <div class="detail-section">
            <h4>分项评分</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="d-label">逻辑思维</span>
                <span class="d-value" :class="getScoreClass(selectedEvaluation.logic_score)">{{ selectedEvaluation.logic_score }}</span>
              </div>
              <div class="detail-item">
                <span class="d-label">创造力</span>
                <span class="d-value" :class="getScoreClass(selectedEvaluation.creativity_score)">{{ selectedEvaluation.creativity_score }}</span>
              </div>
              <div class="detail-item">
                <span class="d-label">表达能力</span>
                <span class="d-value" :class="getScoreClass(selectedEvaluation.expression_score)">{{ selectedEvaluation.expression_score }}</span>
              </div>
              <div class="detail-item">
                <span class="d-label">知识广度</span>
                <span class="d-value" :class="getScoreClass(selectedEvaluation.knowledge_score)">{{ selectedEvaluation.knowledge_score }}</span>
              </div>
            </div>
          </div>

          <div v-if="selectedEvaluation.feedback" class="detail-section">
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

const getToken = () => localStorage.getItem('token')

const formatTime = (ts) => new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })

const formatDate = (ts) => {
  const d = new Date(ts), t = new Date(), y = new Date(t)
  y.setDate(y.getDate() - 1)
  if (d.toDateString() === t.toDateString()) return '今天'
  if (d.toDateString() === y.toDateString()) return '昨天'
  return d.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })
}

const formatFullTime = (ts) => new Date(ts).toLocaleString('zh-CN')

const getScoreClass = (score) => {
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 60) return 'average'
  return 'poor'
}

const loadEvaluations = async () => {
  const token = getToken()
  if (!token) { alert('请先登录'); return }
  loading.value = true
  try {
    const res = await fetch('http://localhost:5000/api/evaluations', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) throw new Error('获取失败')
    evaluations.value = await res.json()
  } catch (e) { console.error(e); alert('获取评分记录失败') }
  finally { loading.value = false }
}

const viewEvaluation = (evaluation) => { selectedEvaluation.value = evaluation }
const closeModal = () => { selectedEvaluation.value = null }

onMounted(() => { loadEvaluations() })
</script>

<style scoped>
.evaluations-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgba(7,11,20,0.6);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  overflow: hidden;
}

.evaluations-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(13,20,33,0.6);
  border-bottom: 1px solid rgba(255,255,255,0.06);
  backdrop-filter: blur(12px);
}

.evaluations-header h2 {
  font-family: 'Orbitron', sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: #e8eaed;
  letter-spacing: 1px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  color: #5a6275;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  cursor: pointer;
  transition: all 0.3s;
}

.refresh-btn:hover {
  background: rgba(0,229,255,0.08);
  color: #00e5ff;
  border-color: rgba(0,229,255,0.2);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #5a6275;
  font-size: 13px;
  gap: 12px;
}

.loader {
  width: 28px; height: 28px;
  border: 2px solid rgba(0,229,255,0.1);
  border-top-color: #00e5ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  text-align: center;
  gap: 12px;
}

.empty-title { font-size: 16px; font-weight: 600; color: #e8eaed; }
.empty-hint { font-size: 13px; color: #5a6275; }

.evaluations-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  align-content: start;
}

.evaluation-card {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  padding: 20px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.evaluation-card:hover {
  border-color: rgba(0,229,255,0.15);
  background: rgba(255,255,255,0.03);
  box-shadow: 0 0 30px rgba(0,229,255,0.04);
  transform: translateY(-2px);
}

.card-accent {
  position: absolute; top: 0; left: 0;
  width: 100%; height: 2px;
  background: linear-gradient(90deg, transparent, rgba(0,229,255,0.3), transparent);
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 8px 12px;
  background: rgba(0,229,255,0.04);
  border: 1px solid rgba(0,229,255,0.06);
  border-radius: 8px;
}

.card-date { font-size: 12px; font-weight: 600; color: #00e5ff; letter-spacing: 0.5px; }
.card-time { font-size: 11px; color: #5a6275; }

.card-score-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 4px;
}

.score-label { font-size: 13px; color: #8892a4; }

.score-big {
  font-family: 'Orbitron', sans-serif;
  font-size: 28px;
  font-weight: 700;
}

.score-big.excellent { color: #00e676; }
.score-big.good { color: #00e5ff; }
.score-big.average { color: #ffab00; }
.score-big.poor { color: #ff1744; }

.card-scores {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.card-score-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  background: rgba(255,255,255,0.02);
  border-radius: 6px;
}

.cs-label { font-size: 10px; color: #5a6275; text-transform: uppercase; letter-spacing: 0.5px; }
.cs-value { font-family: 'Orbitron', sans-serif; font-size: 16px; font-weight: 600; }

.cs-value.excellent { color: #00e676; }
.cs-value.good { color: #00e5ff; }
.cs-value.average { color: #ffab00; }
.cs-value.poor { color: #ff1744; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 20px;
}

.modal {
  background: rgba(13,20,33,0.96);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(0,229,255,0.1);
  border-radius: 16px;
  max-width: 640px;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.modal-header h3 { font-family: 'Orbitron', sans-serif; font-size: 13px; color: #e8eaed; letter-spacing: 0.5px; }
.close-btn { background: none; border: none; color: #5a6275; font-size: 24px; cursor: pointer; }

.modal-body { padding: 24px; }

.modal-info {
  padding: 12px 16px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  margin-bottom: 24px;
}

.info-row { display: flex; justify-content: space-between; align-items: center; }
.info-label { font-size: 12px; color: #5a6275; }
.info-value { font-size: 12px; color: #e8eaed; font-weight: 500; }

.detail-section { margin-bottom: 24px; }
.detail-section h4 { font-family: 'Orbitron', sans-serif; font-size: 12px; color: #e8eaed; letter-spacing: 0.5px; margin-bottom: 12px; }

.overall-large {
  font-family: 'Orbitron', sans-serif;
  font-size: 56px;
  font-weight: 800;
  text-align: center;
  padding: 20px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px;
}

.overall-large.excellent { color: #00e676; }
.overall-large.good { color: #00e5ff; }
.overall-large.average { color: #ffab00; }
.overall-large.poor { color: #ff1744; }

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
}

.d-label { font-size: 12px; color: #5a6275; }
.d-value { font-family: 'Orbitron', sans-serif; font-size: 20px; font-weight: 600; }

.d-value.excellent { color: #00e676; }
.d-value.good { color: #00e5ff; }
.d-value.average { color: #ffab00; }
.d-value.poor { color: #ff1744; }

.feedback-text {
  font-size: 13px;
  line-height: 1.7;
  color: #8892a4;
  padding: 14px;
  background: rgba(255,255,255,0.02);
  border-left: 2px solid rgba(0,229,255,0.3);
  border-radius: 0 8px 8px 0;
}

.evaluations-list::-webkit-scrollbar { width: 4px; }
.evaluations-list::-webkit-scrollbar-thumb { background: rgba(0,229,255,0.1); border-radius: 2px; }

@media (max-width: 768px) {
  .evaluations-list { padding: 18px; grid-template-columns: 1fr; }
  .detail-grid { grid-template-columns: 1fr; }
}
</style>

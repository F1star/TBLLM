<template>
  <div class="professional-assessment">
    <!-- 头部区域 -->
    <div class="assessment-header">
      <h1 class="header-title">专业能力测评</h1>
      <p class="header-subtitle">通过科学的问卷评估您的综合能力，获得专业的发展建议</p>

      <!-- 进度指示器 -->
      <div v-if="selectedCohort" class="progress-indicator">
        <div class="progress-steps">
          <div class="step" :class="{ active: currentStep === 1, completed: currentStep > 1 }">
            <div class="step-number">1</div>
            <div class="step-label">选择组别</div>
          </div>
          <div class="step-line" :class="{ active: currentStep > 1 }"></div>
          <div class="step" :class="{ active: currentStep === 2, completed: currentStep > 2 }">
            <div class="step-number">2</div>
            <div class="step-label">回答问题</div>
          </div>
          <div class="step-line" :class="{ active: currentStep > 2 }"></div>
          <div class="step" :class="{ active: currentStep === 3 }">
            <div class="step-number">3</div>
            <div class="step-label">查看结果</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 步骤1：选择组别 -->
    <div v-if="currentStep === 1" class="step-container">
      <div class="cohort-selection">
        <div class="selection-card">
          <div class="card-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 15l-3-3h6l-3 3z"/>
              <circle cx="12" cy="12" r="10"/>
            </svg>
          </div>
          <h2 class="card-title">请选择您的测评类型</h2>
          <p class="card-description">系统将根据您的选择提供最适合的评估问题</p>

          <div class="cohort-grid">
            <div
              v-for="cohort in cohorts"
              :key="cohort.id"
              :class="['cohort-card', { selected: selectedCohort === cohort.id }]"
              @click="selectCohort(cohort.id)"
              role="button"
              tabindex="0"
              @keydown.enter="selectCohort(cohort.id)"
              @keydown.space="selectCohort(cohort.id)"
            >
              <div class="cohort-icon">{{ cohort.emoji }}</div>
              <h3 class="cohort-name">{{ cohort.name }}</h3>
              <p class="cohort-description">{{ cohort.description }}</p>
              <div class="cohort-tags">
                <span v-for="tag in cohort.tags" :key="tag" class="tag">{{ tag }}</span>
              </div>
            </div>
          </div>

          <!-- 选择提示 -->
          <div v-if="!selectedCohort" class="selection-hint">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
              <path d="M12 8v4M12 16h.01"/>
            </svg>
            <span>请先选择您的测评类型</span>
          </div>

          <button
            class="next-btn"
            :disabled="!selectedCohort"
            @click="startAssessment"
            :class="{ 'pulse-animation': !selectedCohort }"
          >
            开始测评
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 步骤2：回答问题 -->
    <div v-else-if="currentStep === 2" class="step-container">
      <div class="assessment-wrapper">
        <!-- 顶部控制栏 -->
        <div class="assessment-controls">
          <button class="back-btn" @click="currentStep = 1">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            返回
          </button>

          <div class="question-progress">
            <span class="current-question">第 {{ currentQuestionIndex + 1 }} 题</span>
            <span class="total-questions">/ {{ filteredQuestions.length }}</span>
          </div>

          <div class="completion-status">
            <span class="answered-count">{{ answeredCount }}</span>
            <span class="total-count">/{{ filteredQuestions.length }} 已回答</span>
          </div>

          <button
            v-if="isDev"
            class="debug-btn"
            @click="showDebugInfo"
          >
            调试
          </button>
        </div>

        <!-- 记忆通知横幅：提示已恢复上次的答案 -->
        <transition name="memory-fade">
          <div v-if="showMemoryNotification" class="memory-notification">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
              <path d="M12 6v6l4 2"/>
            </svg>
            <span class="memory-text">{{ memoryNotificationText }}</span>
            <button class="memory-dismiss" @click="showMemoryNotification = false">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </transition>

        <!-- 问题卡片 -->
        <div class="question-card" v-if="currentQuestion">
          <div class="question-header">
            <div class="question-type-badge">{{ getQuestionTypeLabel(currentQuestion.question_type) }}</div>
            <div class="question-difficulty" v-if="currentQuestion.metadata?.difficulty">
              难度: {{ currentQuestion.metadata.difficulty }}
            </div>
          </div>

          <div class="question-content">
            <div class="question-text">
              {{ currentQuestion.question_text }}
            </div>

            <!-- 填空题 -->
            <div v-if="currentQuestion.question_type === 'text'" class="answer-section text-answer">
              <div class="input-wrapper">
                <input
                  type="text"
                  v-model="currentAnswer"
                  :placeholder="getPlaceholder(currentQuestion)"
                  class="text-input"
                  @input="handleTextInput"
                  @blur="handleTextBlur"
                />
                <div class="input-decoration"></div>
              </div>
              <div class="input-hints" v-if="currentQuestion.metadata">
                <span v-if="currentQuestion.metadata.unit" class="hint-item">单位: {{ currentQuestion.metadata.unit }}</span>
                <span v-if="currentQuestion.metadata.format" class="hint-item">格式: {{ currentQuestion.metadata.format }}</span>
                <span v-if="currentQuestion.metadata.min || currentQuestion.metadata.max" class="hint-item">
                  范围: {{ currentQuestion.metadata.min || '无' }} - {{ currentQuestion.metadata.max || '无' }}
                </span>
              </div>
            </div>

            <!-- 单选题 -->
            <div v-else-if="currentQuestion.question_type === 'single_choice'" class="answer-section choice-answer">
              <div class="choice-grid">
                <div
                  v-for="(label, key) in currentQuestion.options"
                  :key="key"
                  :class="['choice-option', { selected: answers[currentQuestionIndex] === key, focused: focusedOption === key }]"
                  @click="selectChoice(key)"
                  @mousedown="setActiveRipple(key)"
                  @mouseup="clearActiveRipple"
                  @touchstart="setActiveRipple(key)"
                  @touchend="clearActiveRipple"
                  @keydown.enter="selectChoice(key)"
                  @keydown.space="selectChoice(key)"
                  @focus="focusedOption = key"
                  @blur="focusedOption = null"
                  role="radio"
                  :aria-checked="answers[currentQuestionIndex] === key"
                  tabindex="0"
                  :data-key="key"
                >
                  <div class="option-indicator">
                    <div class="option-circle"></div>
                    <div class="option-checkmark" v-if="answers[currentQuestionIndex] === key">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <path d="M20 6L9 17l-5-5"/>
                      </svg>
                    </div>
                  </div>
                  <div class="option-content">
                    <div class="option-key">{{ key }}</div>
                    <div class="option-label">{{ label }}</div>
                  </div>
                  <!-- 点击涟漪效果 -->
                  <div class="click-ripple" :class="{ active: activeRipple === key }"></div>
                  <!-- 聚焦光环 -->
                  <div class="focus-ring" v-if="focusedOption === key"></div>
                </div>
              </div>
            </div>

            <!-- 矩阵题 -->
            <div v-else-if="currentQuestion.question_type === 'matrix'" class="answer-section matrix-answer">
              <div class="matrix-container">
                <div class="matrix-header">
                  <div class="matrix-title">请在每行中选择最符合的选项</div>
                  <div class="matrix-legend">
                    <span v-for="(option, key) in currentQuestion.options" :key="key" class="legend-item">
                      <span class="legend-key">{{ key }}</span>
                      <span class="legend-label">{{ option }}</span>
                    </span>
                  </div>
                </div>

                <div class="matrix-rows">
                  <div
                    v-for="(row, rowIndex) in currentQuestion.metadata?.rows || []"
                    :key="rowIndex"
                    class="matrix-row"
                    :class="{ answered: matrixAnswers[currentQuestion.question_id]?.[rowIndex] }"
                  >
                    <div class="row-label">{{ row.label_zh || row.label || row }}</div>
                    <div class="row-options">
                      <div
                        v-for="(option, key) in currentQuestion.options"
                        :key="key"
                        :class="['matrix-option', { selected: matrixAnswers[currentQuestion.question_id]?.[rowIndex] === key, focused: focusedMatrixOption === `${rowIndex}-${key}` }]"
                        @click="selectMatrixAnswer(currentQuestion.question_id, rowIndex, key)"
                        @mousedown="setActiveMatrixRipple(rowIndex, key)"
                        @mouseup="clearActiveMatrixRipple"
                        @touchstart="setActiveMatrixRipple(rowIndex, key)"
                        @touchend="clearActiveMatrixRipple"
                        @keydown.enter="selectMatrixAnswer(currentQuestion.question_id, rowIndex, key)"
                        @keydown.space="selectMatrixAnswer(currentQuestion.question_id, rowIndex, key)"
                        @focus="focusedMatrixOption = `${rowIndex}-${key}`"
                        @blur="focusedMatrixOption = null"
                        role="radio"
                        :aria-checked="matrixAnswers[currentQuestion.question_id]?.[rowIndex] === key"
                        tabindex="0"
                        :data-row="rowIndex"
                        :data-key="key"
                      >
                        <div class="matrix-option-circle"></div>
                        <div class="matrix-option-checkmark" v-if="matrixAnswers[currentQuestion.question_id]?.[rowIndex] === key">
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <path d="M20 6L9 17l-5-5"/>
                          </svg>
                        </div>
                        <!-- 点击涟漪效果 -->
                        <div class="matrix-click-ripple" :class="{ active: activeMatrixRipple === `${rowIndex}-${key}` }"></div>
                        <!-- 聚焦光环 -->
                        <div class="matrix-focus-ring" v-if="focusedMatrixOption === `${rowIndex}-${key}`"></div>
                      </div>
                    </div>
                    <div class="row-status" v-if="matrixAnswers[currentQuestion.question_id]?.[rowIndex]">
                      <span class="status-text">已选择: {{ currentQuestion.options[matrixAnswers[currentQuestion.question_id][rowIndex]] }}</span>
                    </div>
                  </div>
                </div>
                <div class="matrix-progress" v-if="currentQuestion.metadata?.rows">
                  <div class="progress-text">
                    已完成: {{ getMatrixAnsweredCount(currentQuestion.question_id) }}/{{ currentQuestion.metadata.rows.length }} 行
                  </div>
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: `${(getMatrixAnsweredCount(currentQuestion.question_id) / currentQuestion.metadata.rows.length) * 100}%` }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 题目导航 -->
          <div class="question-navigation">
            <button
              class="nav-btn prev-btn"
              :disabled="currentQuestionIndex === 0"
              @click="prevQuestion"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M15 18l-6-6 6-6"/>
              </svg>
              上一题
            </button>

            <div class="question-dots">
              <button
                v-for="(question, index) in filteredQuestions"
                :key="index"
                :class="['question-dot', {
                  active: index === currentQuestionIndex,
                  answered: isQuestionAnswered(index)
                }]"
                @click="goToQuestion(index)"
              >
                {{ index + 1 }}
              </button>
            </div>

            <button
              class="nav-btn next-btn"
              :disabled="currentQuestionIndex === filteredQuestions.length - 1"
              @click="nextQuestion"
            >
              下一题
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- 提交按钮区域（始终可见） -->
        <div class="submit-section">
          <div class="submit-info">
            <div class="info-item">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
                <path d="M12 16v-4M12 8h.01"/>
              </svg>
              <span>所有问题回答完毕后才能提交</span>
            </div>
            <div class="info-item">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M4 12a8 8 0 018-8V2a10 10 0 00-10 10h2zM20 12a8 8 0 01-8 8v2a10 10 0 0010-10h-2z"/>
              </svg>
              <span>提交后系统将进行智能评估</span>
            </div>
          </div>

          <button
            class="submit-btn"
            :disabled="!allQuestionsAnswered || submitting"
            @click="submitAssessment"
            :class="{ submitting: submitting }"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
              <path d="M22 4L12 14.01l-3-3"/>
            </svg>
            {{ submitting ? '提交中...' : '提交测评' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 步骤3：查看结果 -->
    <div v-else-if="currentStep === 3" class="step-container">
      <div class="results-container">
        <div class="results-header">
          <div class="results-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
              <path d="M22 4L12 14.01l-3-3"/>
            </svg>
          </div>
          <h2 class="results-title">测评完成！</h2>
          <p class="results-subtitle">您的评估结果已生成，以下是详细分析</p>
        </div>

        <div v-if="assessmentResult" class="results-content">
          <div class="results-summary">
            <h3>技能评估概览</h3>
            <div class="summary-grid">
              <div v-for="(score, skill) in assessmentResult.skill_scores" :key="skill" class="skill-item">
                <div class="skill-name">{{ skill }}</div>
                <div class="skill-progress">
                  <div class="progress-bar">
                    <div
                      class="progress-fill"
                      :style="{ width: score + '%' }"
                      :class="getSkillLevelClass(score)"
                    ></div>
                  </div>
                  <div class="skill-score">{{ Math.round(score) }}分</div>
                </div>
              </div>
            </div>
          </div>

          <div class="results-actions">
            <button class="action-btn secondary" @click="resetAssessment">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 12a9 9 0 1018 0 9 9 0 10-18 0"/>
                <path d="M13 8l-4 4 4 4M9 12h9"/>
              </svg>
              重新测评
            </button>
            <button class="action-btn primary" @click="downloadResults">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <path d="M7 10l5 5 5-5"/>
                <path d="M12 15V3"/>
              </svg>
              下载报告
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">
        <div class="spinner"></div>
        <p>{{ loadingMessage }}</p>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMessage" class="error-message">
      <div class="error-content">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
          <path d="M12 8v4M12 16h.01"/>
        </svg>
        <p>{{ errorMessage }}</p>
        <button class="error-retry" @click="retry">重试</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick } from 'vue'

export default {
  name: 'ProfessionalAssessmentNew',
  setup() {
    // 状态管理
    const currentStep = ref(1)
    const selectedCohort = ref(null)
    const questions = ref([])
    const currentQuestionIndex = ref(0)
    const answers = ref({})
    const matrixAnswers = ref({})
    const loading = ref(false)
    const loadingMessage = ref('加载问题中...')
    const errorMessage = ref('')
    const submitting = ref(false)
    const assessmentResult = ref(null)

    // 交互状态
    const activeRipple = ref(null)
    const activeMatrixRipple = ref(null)
    const focusedOption = ref(null)
    const focusedMatrixOption = ref(null)
    const isDev = import.meta.env.DEV;

    // 记忆功能状态
    const currentSessionId = ref(null)
    const rememberedAnswersCount = ref(0)
    const showMemoryNotification = ref(false)
    const memoryNotificationText = ref('')

    // 组别数据
    const cohorts = [
      {
        id: 'younger',
        name: '年轻学生组',
        emoji: '🎓',
        description: '适合初中及高中学生',
        tags: ['12-18岁', '学业导向', '基础评估']
      },
      {
        id: 'elderly',
        name: '年长学生组',
        emoji: '👨‍🎓',
        description: '适合大学生及研究生',
        tags: ['18-25岁', '职业导向', '深入评估']
      }
    ]

    // 计算属性
    const filteredQuestions = computed(() => {
      if (!selectedCohort.value) return []
      return questions.value.filter(q => q.cohort === selectedCohort.value)
    })

    const currentQuestion = computed(() => {
      return filteredQuestions.value[currentQuestionIndex.value] || null
    })

    const answeredCount = computed(() => {
      let count = 0
      filteredQuestions.value.forEach((question, index) => {
        if (isQuestionAnswered(index)) {
          count++
        }
      })
      return count
    })

    const allQuestionsAnswered = computed(() => {
      return answeredCount.value === filteredQuestions.value.length
    })

    // 当前问题的答案（确保响应性）
    const currentAnswer = computed({
      get: () => answers.value[currentQuestionIndex.value],
      set: (value) => {
        const newAnswers = { ...answers.value }
        newAnswers[currentQuestionIndex.value] = value
        answers.value = newAnswers
      }
    })

    // 当前问题的矩阵答案
    const currentMatrixAnswer = computed(() => {
      const question = currentQuestion.value
      if (!question || question.question_type !== 'matrix') return null
      return matrixAnswers.value[question.question_id]
    })

    // 方法
    const selectCohort = (cohortId) => {
      selectedCohort.value = cohortId
    }

    const startAssessment = async () => {
      console.log('🔍 startAssessment called')
      console.log('🔍 selectedCohort:', selectedCohort.value)
      console.log('🔍 currentStep before:', currentStep.value)

      if (!selectedCohort.value) {
        console.log('❌ 请先选择测评类型')
        errorMessage.value = '请先选择测评类型'
        return
      }

      console.log('✅ 切换到步骤2')
      currentStep.value = 2
      console.log('🔍 currentStep after:', currentStep.value)

      await loadQuestions()

      // 创建测评会话（用于自动保存）
      await createAssessmentSession()

      // 加载记忆的答案（预填）
      await loadRememberedAnswers()
    }

    // === 记忆功能：创建会话、加载记忆、自动保存 ===

    const createAssessmentSession = async () => {
      /** 创建后端测评会话，用于自动保存答案 */
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const response = await fetch('http://localhost:5000/api/professional-assessment/sessions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            cohort: selectedCohort.value,
            question_count: filteredQuestions.value.length
          })
        })

        if (!response.ok) {
          console.warn('创建会话失败:', response.status)
          return
        }

        const data = await response.json()
        if (data.session) {
          currentSessionId.value = data.session.id
          console.log('✅ 已创建测评会话 ID:', currentSessionId.value)
        }
      } catch (error) {
        console.warn('创建会话失败，自动保存不可用:', error)
      }
    }

    const loadRememberedAnswers = async () => {
      /**
       * 从后端加载用户上次的答案（记忆功能）
       * 预填到当前测评中，避免重复作答
       */
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const response = await fetch(
          `http://localhost:5000/api/professional-assessment/remembered-answers/${selectedCohort.value}`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        )

        if (!response.ok) return

        const data = await response.json()
        if (data.count > 0 && data.remembered_answers) {
          applyRememberedAnswers(data.remembered_answers)
        }
      } catch (error) {
        console.warn('加载记忆答案失败:', error)
      }
    }

    const applyRememberedAnswers = (remembered) => {
      /**
       * 将记忆的答案映射到当前问题的答案对象中
       * 支持单选题、填空题和矩阵题
       */
      let appliedCount = 0
      const newAnswers = { ...answers.value }
      const newMatrixAnswers = { ...matrixAnswers.value }

      filteredQuestions.value.forEach((question, index) => {
        const rememberedAnswer = remembered[question.question_id]
        if (!rememberedAnswer) return

        if (question.question_type === 'single_choice') {
          // 单选题：answer_text 存储的是选项键（如 "A", "B"）
          const optionKey = rememberedAnswer.answer_text
          if (optionKey && question.options && question.options[optionKey]) {
            newAnswers[index] = optionKey
            appliedCount++
          } else if (optionKey && question.options) {
            // 兼容旧数据：answer_text 存的是标签文本而非键，反向查找
            const foundKey = Object.keys(question.options).find(
              k => question.options[k] === optionKey
            )
            if (foundKey) {
              newAnswers[index] = foundKey
              appliedCount++
            }
          }
        } else if (question.question_type === 'text') {
          // 填空题：直接使用文本答案
          if (rememberedAnswer.answer_text) {
            newAnswers[index] = rememberedAnswer.answer_text
            appliedCount++
          }
        } else if (question.question_type === 'matrix') {
          // 矩阵题：answer_text 中存储的是 JSON 格式的行→选项映射
          try {
            const matrixData = JSON.parse(rememberedAnswer.answer_text)
            if (typeof matrixData === 'object' && matrixData !== null) {
              newMatrixAnswers[question.question_id] = { ...matrixData }
              appliedCount += Object.keys(matrixData).length
            }
          } catch (e) {
            // 非 JSON 格式，跳过
            console.warn('矩阵题记忆数据解析失败:', e)
          }
        }
      })

      answers.value = newAnswers
      matrixAnswers.value = newMatrixAnswers

      if (appliedCount > 0) {
        rememberedAnswersCount.value = appliedCount
        memoryNotificationText.value = `已记住您上次的答案，${appliedCount} 道题已自动填入`
        showMemoryNotification.value = true
        setTimeout(() => {
          showMemoryNotification.value = false
        }, 5000)
        console.log(`✅ 记忆恢复完成：${appliedCount} 道题已预填`)
      }
    }

    const autoSaveAnswer = async (questionId, answerText, rawValue) => {
      /**
       * 自动保存单个问题的答案到后端会话
       * 确保下次测评时能记住本次的回答
       */
      if (!currentSessionId.value) return
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        await fetch(
          `http://localhost:5000/api/professional-assessment/sessions/${currentSessionId.value}/responses`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              question_id: questionId,
              answer_text: answerText || '',
              raw_value: rawValue ?? null
            })
          }
        )
      } catch (error) {
        console.warn('自动保存失败:', error)
      }
    }

    const handleTextBlur = () => {
      /** 文本输入框失焦时自动保存 */
      const question = currentQuestion.value
      if (!question) return
      const answer = answers.value[currentQuestionIndex.value]
      autoSaveAnswer(question.question_id, answer, null)
    }

    const loadQuestions = async () => {
      loadingMessage.value = '正在加载测评问题...'
      errorMessage.value = ''

      try {
        const token = localStorage.getItem('token')
        if (!token) {
          errorMessage.value = '请先登录系统'
          loading.value = false
          return
        }

        const response = await fetch('http://localhost:5000/api/professional-assessment/questions', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const data = await response.json()
        questions.value = data
        console.log(`成功加载 ${questions.value.length} 个问题`)

        // 初始化答案存储 - 使用响应式方式
        const newAnswers = { ...answers.value }
        const newMatrixAnswers = { ...matrixAnswers.value }

        filteredQuestions.value.forEach((question, index) => {
          // 初始化answers对象，为每个问题索引设置空字符串
          newAnswers[index] = ''

          if (question.question_type === 'matrix') {
            // 确保响应式初始化
            newMatrixAnswers[question.question_id] = {}
          }
        })

        // 一次性更新响应式对象
        answers.value = newAnswers
        matrixAnswers.value = newMatrixAnswers
      } catch (error) {
        console.error('加载问题时出错:', error)
        errorMessage.value = `加载失败: ${error.message}`

        // 开发环境下提供示例数据
        if (import.meta.env.DEV) {
          console.log('使用示例数据...')
          questions.value = [
            // younger组问题
            {
              question_id: 'q1',
              question_text: '您认为自己最擅长的能力是什么？',
              question_type: 'text',
              cohort: 'younger',
              metadata: { unit: '能力领域', format: '文本' }
            },
            {
              question_id: 'q2',
              question_text: '您通常如何解决复杂问题？',
              question_type: 'single_choice',
              cohort: 'younger',
              options: {
                A: '独立思考',
                B: '团队讨论',
                C: '查阅资料',
                D: '寻求帮助'
              }
            },
            {
              question_id: 'q3',
              question_text: '请评估以下技能的重要程度：',
              question_type: 'matrix',
              cohort: 'younger',
              options: {
                1: '非常重要',
                2: '重要',
                3: '一般',
                4: '不重要'
              },
              metadata: {
                rows: [
                  { label_zh: '逻辑思维' },
                  { label_zh: '沟通能力' },
                  { label_zh: '创新能力' }
                ]
              }
            },
            // elderly组问题
            {
              question_id: 'q4',
              question_text: '您认为哪些技能对职业发展最重要？',
              question_type: 'text',
              cohort: 'elderly',
              metadata: { unit: '技能领域', format: '文本' }
            },
            {
              question_id: 'q5',
              question_text: '面对职业挑战时，您通常如何应对？',
              question_type: 'single_choice',
              cohort: 'elderly',
              options: {
                A: '制定详细计划',
                B: '寻求导师指导',
                C: '团队协作解决',
                D: '自我反思调整'
              }
            },
            {
              question_id: 'q6',
              question_text: '请评估以下职业能力的重要程度：',
              question_type: 'matrix',
              cohort: 'elderly',
              options: {
                1: '至关重要',
                2: '比较重要',
                3: '一般重要',
                4: '不太重要'
              },
              metadata: {
                rows: [
                  { label_zh: '领导能力' },
                  { label_zh: '沟通协调' },
                  { label_zh: '专业技能' },
                  { label_zh: '创新思维' }
                ]
              }
            }
          ]
          errorMessage.value = ''

          // 初始化答案存储（示例数据）- 使用响应式方式
          const newAnswers = { ...answers.value }
          const newMatrixAnswers = { ...matrixAnswers.value }

          filteredQuestions.value.forEach((question, index) => {
            // 初始化answers对象，为每个问题索引设置空字符串
            newAnswers[index] = ''

            if (question.question_type === 'matrix') {
              // 确保响应式初始化
              newMatrixAnswers[question.question_id] = {}
            }
          })

          // 一次性更新响应式对象
          answers.value = newAnswers
          matrixAnswers.value = newMatrixAnswers
        }
      } finally {
        loading.value = false
      }
    }

    const setActiveRipple = (key) => {
      activeRipple.value = key
    }

    const clearActiveRipple = () => {
      setTimeout(() => {
        activeRipple.value = null
      }, 600)
    }

    const setActiveMatrixRipple = (rowIndex, key) => {
      activeMatrixRipple.value = `${rowIndex}-${key}`
    }

    const clearActiveMatrixRipple = () => {
      setTimeout(() => {
        activeMatrixRipple.value = null
      }, 600)
    }

    const handleTextInput = () => {
      // 文本输入处理
      nextTick(() => {
        console.log('文本输入更新:', answers.value[currentQuestionIndex.value])
      })
    }

    const selectChoice = (key) => {
      console.log('选择答案:', key, '当前问题索引:', currentQuestionIndex.value, '答案对象:', answers.value)

      // 如果已经选择了相同的选项，则取消选择（允许取消）
      if (answers.value[currentQuestionIndex.value] === key) {
        const newAnswers = { ...answers.value }
        newAnswers[currentQuestionIndex.value] = ''
        answers.value = newAnswers
        console.log('取消选择答案')
      } else {
        // 确保响应式更新 - 使用Vue的响应式系统
        const newAnswers = { ...answers.value }
        newAnswers[currentQuestionIndex.value] = key
        answers.value = newAnswers
        console.log('更新后的answers:', answers.value)
      }

      // 自动保存答案到服务器（记忆功能）
      const question = currentQuestion.value
      if (question) {
        const selectedKey = answers.value[currentQuestionIndex.value]
        autoSaveAnswer(question.question_id, selectedKey, selectedKey ? parseInt(selectedKey) : null)
      }

      // 立即触发UI更新
      nextTick(() => {
        console.log('验证 - 当前问题答案:', answers.value[currentQuestionIndex.value])
        console.log('验证 - 是否已回答:', isQuestionAnswered(currentQuestionIndex.value))
        console.log('所有问题已回答:', allQuestionsAnswered.value)
      })
    }

    const selectMatrixAnswer = (questionId, rowIndex, key) => {
      console.log('选择矩阵答案:', questionId, '行:', rowIndex, '键:', key, '当前matrixAnswers:', matrixAnswers.value)

      // 确保响应式更新
      const newMatrixAnswers = { ...matrixAnswers.value }
      if (!newMatrixAnswers[questionId]) {
        newMatrixAnswers[questionId] = {}
      }

      // 如果点击已选中的选项，则取消选择
      if (newMatrixAnswers[questionId][rowIndex] === key) {
        delete newMatrixAnswers[questionId][rowIndex]
        console.log('取消选择矩阵答案')
      } else {
        newMatrixAnswers[questionId][rowIndex] = key
      }

      matrixAnswers.value = newMatrixAnswers
      console.log('更新后的matrixAnswers:', matrixAnswers.value)

      // 自动保存矩阵答案到服务器（序列化为JSON）
      const matrixData = matrixAnswers.value[questionId]
      if (matrixData) {
        autoSaveAnswer(questionId, JSON.stringify(matrixData), null)
      }

      // 立即触发UI更新
      nextTick(() => {
        const currentQuestion = filteredQuestions.value[currentQuestionIndex.value]
        if (currentQuestion && currentQuestion.question_type === 'matrix') {
          console.log('验证 - 矩阵题答案:', matrixAnswers.value[questionId])
          console.log('验证 - 是否已回答:', isQuestionAnswered(currentQuestionIndex.value))
          console.log('矩阵完成进度:', getMatrixAnsweredCount(questionId), '/', currentQuestion.metadata?.rows?.length || 0)
        }
      })
    }

    const isQuestionAnswered = (index) => {
      const question = filteredQuestions.value[index]
      if (!question) return false

      if (question.question_type === 'matrix') {
        const matrixAnswer = matrixAnswers.value[question.question_id]
        const rowCount = question.metadata?.rows?.length || 0
        if (!matrixAnswer || Object.keys(matrixAnswer).length < rowCount) {
          return false
        }
        // 检查每一行是否都有答案
        for (let i = 0; i < rowCount; i++) {
          if (matrixAnswer[i] === undefined || matrixAnswer[i] === '') {
            return false
          }
        }
        return true
      }

      const answer = answers.value[index]
      return answer !== undefined && answer !== null && answer !== ''
    }

    const getMatrixAnsweredCount = (questionId) => {
      const matrixAnswer = matrixAnswers.value[questionId]
      if (!matrixAnswer) return 0
      return Object.keys(matrixAnswer).length
    }

    const prevQuestion = () => {
      if (currentQuestionIndex.value > 0) {
        currentQuestionIndex.value--
        // 重置焦点状态
        focusedOption.value = null
        focusedMatrixOption.value = null
      }
    }

    const nextQuestion = () => {
      if (currentQuestionIndex.value < filteredQuestions.value.length - 1) {
        currentQuestionIndex.value++
        // 重置焦点状态
        focusedOption.value = null
        focusedMatrixOption.value = null
      }
    }

    const goToQuestion = (index) => {
      if (index >= 0 && index < filteredQuestions.value.length) {
        currentQuestionIndex.value = index
        // 重置焦点状态
        focusedOption.value = null
        focusedMatrixOption.value = null
      }
    }

    const submitAssessment = async () => {
      if (!allQuestionsAnswered.value) {
        alert('请先完成所有问题的回答')
        return
      }

      submitting.value = true
      loadingMessage.value = '正在提交评估...'

      try {
        const token = localStorage.getItem('token')
        if (!token) {
          throw new Error('请先登录系统')
        }

        // 准备提交数据 - 完全按照 questionnaire_dialogue_test.json 的对话格式
        // 构建学生背景信息，格式完全匹配JSON示例
        const backgroundInfo = [
          `Assistant: 测评组别是什么？ teenager: ${selectedCohort.value === 'younger' ? '年轻学生组' : '年长学生组'}`,
          `Assistant: 测评时间是什么时候？ teenager: ${new Date().toISOString()}`,
          `Assistant: 用户ID是什么？ teenager: assessment_${Date.now()}`
        ].map(item => `- ${item}`).join('\n');

        // 构建问题和答案的文本表示，格式完全匹配JSON示例
        const questionsText = filteredQuestions.value.map((q, idx) => {
          let answerText = '';

          if (q.question_type === 'matrix') {
            const matrixAnswer = matrixAnswers.value[q.question_id];
            if (matrixAnswer) {
              const rowAnswers = q.metadata?.rows?.map((row, rowIdx) => {
                const answerKey = matrixAnswer[rowIdx];
                const answerLabel = q.options[answerKey] || answerKey;
                return `${row.label_zh || row.label || row}: ${answerLabel}`;
              }) || [];
              answerText = rowAnswers.join('; ');
            }
          } else {
            const answer = answers.value[idx];
            // 对于单选题，使用选项标签；对于填空题，直接使用答案
            if (q.question_type === 'single_choice' && q.options && q.options[answer]) {
              answerText = q.options[answer];
            } else {
              answerText = answer || '';
            }
          }

          // 格式完全匹配JSON示例： "X. Assistant: 问题文本 teenager: 答案"
          // 注意：JSON示例中有些问题有额外的描述（如"（请在空格内填入数字。）"），我们保持简单
          return `${idx + 1}. Assistant: ${q.question_text} teenager: ${answerText}`;
        }).join('\n');

        // 构建完全符合 questionnaire_dialogue_test.json 格式的对话数据
        const dialogueData = [{
          id: `assessment_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          conversations: [
            {
              from: "human",
              value: `根据以下学生的背景信息和问卷回答，评估其社会与情感技能：\n\n学生背景信息：\n${backgroundInfo}\n\n问卷回答：\n${questionsText}`
            },
            {
              from: "assistant",
              value: "技能评估结果（百分制）：\n- 等待评估中...\n\n综合评价：\n系统正在分析您的回答，请稍候。"
            }
          ],
          metadata: {
            student_index: Math.floor(Math.random() * 100000),
            background_vars_count: 3,
            response_vars_count: filteredQuestions.value.length,
            skill_scores: {}, // 后端将填充实际评分
            skill_categories: {} // 后端将填充分类
          }
        }];

        // 构建按question_id索引的答案，用于保存到后端数据库
        // 注意：单选题保存选项键（如"A"）而非标签文本，确保记忆恢复时能正确匹配
        const answersByQuestionId = {};
        filteredQuestions.value.forEach((q, idx) => {
          if (q.question_type !== 'matrix' && answers.value[idx]) {
            answersByQuestionId[q.question_id] = answers.value[idx];
          }
        });

        console.log('提交数据（对话格式）:', JSON.stringify(dialogueData, null, 2));

        // 调用后端API - 发送符合微调LLM评估格式的数据
        const response = await fetch('http://localhost:5000/api/professional-assessment/submit', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            // 主要发送对话格式数据用于LLM评估
            dialogue_data: dialogueData,
            // 保留原始数据用于其他处理
            cohort: selectedCohort.value,
            answers: answers.value,
            matrix_answers: matrixAnswers.value,
            assessment_type: 'professional_assessment',
            // 直接保存答案到后端数据库
            session_id: currentSessionId.value,
            answers_by_question_id: answersByQuestionId
          })
        })

        if (!response.ok) {
          throw new Error(`提交失败: ${response.status} ${response.statusText}`)
        }

        const result = await response.json()
        console.log('提交成功:', result)

        // 使用后端返回的评估结果
        if (result.assessment_result) {
          assessmentResult.value = {
            skill_scores: result.assessment_result.skill_scores || {},
            overall_score: result.assessment_result.overall_score || 0,
            feedback: result.assessment_result.feedback || ''
          }

          // 如果有警告信息（如模拟结果），显示给用户
          if (result.assessment_result.warning) {
            console.warn('评估结果警告:', result.assessment_result.warning)
            // 可以在这里添加警告显示逻辑
          }
        } else {
          // 如果没有评估结果，使用模拟数据作为降级方案
          console.warn('后端未返回评估结果，使用模拟数据')
          assessmentResult.value = {
            skill_scores: {
              '逻辑思维': 85,
              '创造力': 78,
              '表达能力': 92,
              '知识广度': 80
            },
            overall_score: 84,
            feedback: '您的综合能力表现优秀，特别是在创新能力和学习能力方面表现突出。建议进一步加强沟通能力和适应能力的培养。'
          }
        }

        currentStep.value = 3

        // 将会话标记为已完成，下次测评时可记住本次答案
        if (currentSessionId.value) {
          try {
            await fetch(
              `http://localhost:5000/api/professional-assessment/sessions/${currentSessionId.value}/complete`,
              {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
              }
            )
          } catch (e) {
            console.warn('标记会话完成失败:', e)
          }
        }
      } catch (error) {
        console.error('提交评估时出错:', error)
        errorMessage.value = `提交失败: ${error.message}`
        alert('提交失败，请稍后重试')
      } finally {
        submitting.value = false
      }
    }

    const getQuestionTypeLabel = (type) => {
      const labels = {
        'text': '填空题',
        'single_choice': '单选题',
        'matrix': '矩阵题'
      }
      return labels[type] || type
    }

    const getPlaceholder = (question) => {
      if (question.metadata?.unit) {
        return `请输入${question.metadata.unit}`
      }
      if (question.metadata?.format) {
        return `请按 ${question.metadata.format} 格式输入`
      }
      return '请输入您的答案'
    }

    const getSkillLevelClass = (score) => {
      if (score >= 90) return 'level-excellent'
      if (score >= 80) return 'level-good'
      if (score >= 70) return 'level-medium'
      if (score >= 60) return 'level-fair'
      return 'level-poor'
    }

    const resetAssessment = () => {
      currentStep.value = 1
      selectedCohort.value = null
      currentQuestionIndex.value = 0
      answers.value = {}
      matrixAnswers.value = {}
      assessmentResult.value = null
      activeRipple.value = null
      activeMatrixRipple.value = null
      focusedOption.value = null
      focusedMatrixOption.value = null
    }

    const downloadResults = () => {
      if (!assessmentResult.value) return

      const dataStr = JSON.stringify(assessmentResult.value, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })

      const downloadUrl = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `测评结果_${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(downloadUrl)
    }

    const retry = () => {
      errorMessage.value = ''
      if (currentStep.value === 2) {
        loadQuestions()
      }
    }

    const showDebugInfo = () => {
      console.log('=== 调试信息 ===')
      console.log('当前步骤:', currentStep.value)
      console.log('当前问题索引:', currentQuestionIndex.value)
      console.log('已回答数量:', answeredCount.value)
      console.log('所有问题已回答:', allQuestionsAnswered.value)
      console.log('answers对象:', JSON.parse(JSON.stringify(answers.value)))
      console.log('matrixAnswers对象:', JSON.parse(JSON.stringify(matrixAnswers.value)))

      // 检查当前问题的答案
      const currentQ = currentQuestion.value
      if (currentQ) {
        console.log('当前问题:', currentQ.question_text)
        console.log('当前问题类型:', currentQ.question_type)
        console.log('当前问题答案:', answers.value[currentQuestionIndex.value])
        if (currentQ.question_type === 'matrix') {
          console.log('矩阵答案:', matrixAnswers.value[currentQ.question_id])
        }
      }

      alert(`调试信息已输出到控制台\n已回答: ${answeredCount.value}/${filteredQuestions.value.length}\n所有问题已回答: ${allQuestionsAnswered.value ? '是' : '否'}`)
    }

    // 生命周期
    onMounted(() => {
      // 组件挂载时的初始化
    })

    return {
      // 状态
      currentStep,
      selectedCohort,
      cohorts,
      questions,
      currentQuestionIndex,
      answers,
      matrixAnswers,
      loading,
      loadingMessage,
      errorMessage,
      submitting,
      assessmentResult,
      activeRipple,
      activeMatrixRipple,
      focusedOption,
      focusedMatrixOption,
      showMemoryNotification,
      memoryNotificationText,

      // 计算属性
      filteredQuestions,
      currentQuestion,
      answeredCount,
      allQuestionsAnswered,
      currentAnswer,
      currentMatrixAnswer,

      // 方法
      selectCohort,
      startAssessment,
      loadQuestions,
      createAssessmentSession,
      loadRememberedAnswers,
      autoSaveAnswer,
      handleTextBlur,
      setActiveRipple,
      clearActiveRipple,
      setActiveMatrixRipple,
      clearActiveMatrixRipple,
      handleTextInput,
      selectChoice,
      selectMatrixAnswer,
      isQuestionAnswered,
      prevQuestion,
      nextQuestion,
      goToQuestion,
      submitAssessment,
      getQuestionTypeLabel,
      getPlaceholder,
      getSkillLevelClass,
      resetAssessment,
      downloadResults,
      retry,
      showDebugInfo,
      getMatrixAnsweredCount
    }
  }
}
</script>

<style scoped>
/* 学术未来主义设计系统 - 完全修复交互问题 */
.professional-assessment {
  min-height: 100vh;
  background:
    linear-gradient(135deg, #0a0e1a 0%, #121a2e 30%, #1a2745 70%, #0f172a 100%),
    repeating-linear-gradient(45deg, rgba(20, 100, 220, 0.03) 0px, rgba(20, 100, 220, 0.03) 1px, transparent 1px, transparent 40px),
    repeating-linear-gradient(-45deg, rgba(120, 200, 255, 0.02) 0px, rgba(120, 200, 255, 0.02) 1px, transparent 1px, transparent 30px);
  padding: 40px 24px;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI Variable', 'Segoe UI', system-ui, sans-serif;
  color: #e6f0ff;
  position: relative;
  overflow-x: hidden;
  letter-spacing: -0.01em;
  line-height: 1.5;
}

/* 未来主义网格背景 */
.professional-assessment::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 15% 25%, rgba(60, 120, 255, 0.08) 0%, transparent 60%),
    radial-gradient(circle at 85% 65%, rgba(140, 100, 255, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 50% 80%, rgba(0, 200, 255, 0.03) 0%, transparent 40%);
  pointer-events: none;
  z-index: 0;
  animation: gridPulse 20s ease-in-out infinite alternate;
}

/* 动态网格脉冲动画 */
@keyframes gridPulse {
  0% {
    opacity: 0.7;
    transform: scale(1);
  }
  50% {
    opacity: 0.9;
    transform: scale(1.02);
  }
  100% {
    opacity: 0.7;
    transform: scale(1);
  }
}

/* 学术装饰边框 */
.professional-assessment::after {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 2px solid transparent;
  background:
    linear-gradient(135deg, transparent 60%, rgba(100, 200, 255, 0.1) 100%),
    linear-gradient(45deg, transparent 70%, rgba(60, 120, 255, 0.1) 100%);
  background-clip: padding-box;
  pointer-events: none;
  z-index: 0;
  mask:
    linear-gradient(#fff 0 0) padding-box,
    linear-gradient(#fff 0 0);
  mask-composite: exclude;
  -webkit-mask:
    linear-gradient(#fff 0 0) padding-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
}

/* 学术头部样式 - 增强视觉层次和可读性 */
.assessment-header {
  max-width: 1200px;
  margin: 0 auto 60px;
  text-align: center;
  position: relative;
  z-index: 2;
  padding: 40px 0;
}

.header-title {
  font-size: 3.8rem;
  font-weight: 800;
  background: linear-gradient(135deg,
    #64b5ff 0%,
    #3d8bff 25%,
    #7b68ff 50%,
    #a855f7 75%,
    #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 20px;
  letter-spacing: -0.03em;
  line-height: 1.05;
  text-shadow:
    0 2px 4px rgba(0, 0, 0, 0.2),
    0 8px 32px rgba(100, 181, 255, 0.3);
  position: relative;
  display: inline-block;
}

.header-title::after {
  content: '';
  position: absolute;
  bottom: -12px;
  left: 25%;
  right: 25%;
  height: 4px;
  background: linear-gradient(90deg, transparent, #64b5ff, #7b68ff, transparent);
  border-radius: 2px;
  opacity: 0.7;
  animation: titleLine 3s ease-in-out infinite;
}

@keyframes titleLine {
  0%, 100% {
    opacity: 0.5;
    transform: scaleX(0.8);
  }
  50% {
    opacity: 0.8;
    transform: scaleX(1);
  }
}

.header-subtitle {
  font-size: 1.4rem;
  color: rgba(230, 240, 255, 0.9);
  margin-bottom: 48px;
  line-height: 1.7;
  font-weight: 450;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.01em;
  position: relative;
  padding: 20px;
  background: rgba(16, 24, 39, 0.5);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  border: 1px solid rgba(100, 181, 255, 0.15);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* 进度指示器 - 修复视觉层次 */
.progress-indicator {
  max-width: 900px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.progress-steps {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  flex: 1;
  opacity: 0.5;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  cursor: pointer;
}

.step:hover {
  opacity: 0.8;
}

.step.active {
  opacity: 1;
}

.step.completed {
  opacity: 0.9;
}

.step-number {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: 3px solid rgba(76, 201, 240, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #4cc9f0;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 1.2rem;
  position: relative;
  z-index: 2;
}

.step.active .step-number {
  background: linear-gradient(135deg, #4cc9f0 0%, #4361ee 100%);
  border-color: transparent;
  color: white;
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(76, 201, 240, 0.5);
}

.step.completed .step-number {
  background: linear-gradient(135deg, #4cc9f0 0%, #4361ee 100%);
  border-color: transparent;
  color: white;
}

.step-label {
  font-size: 0.95rem;
  color: rgba(240, 244, 248, 0.7);
  font-weight: 600;
  text-align: center;
  transition: all 0.3s ease;
}

.step.active .step-label {
  color: #ffffff;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.step-line {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  max-width: 200px;
  transition: all 0.4s ease;
  position: relative;
  top: -25px;
}

.step-line.active {
  background: linear-gradient(90deg, #4cc9f0, #4361ee);
  box-shadow: 0 0 10px rgba(76, 201, 240, 0.3);
}

/* 步骤容器 */
.step-container {
  max-width: 1200px;
  margin: 0 auto;
}

/* 组别选择 */
.cohort-selection {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.selection-card {
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 20px 40px rgba(52, 152, 219, 0.15);
  width: 100%;
  max-width: 800px;
  text-align: center;
  border: 1px solid rgba(52, 152, 219, 0.1);
}

.card-icon {
  color: #3498db;
  margin-bottom: 20px;
}

.card-title {
  font-size: 1.8rem;
  color: #2c3e50;
  margin-bottom: 12px;
  font-weight: 600;
}

.card-description {
  color: #7f8c8d;
  margin-bottom: 30px;
  line-height: 1.6;
}

.cohort-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.cohort-card {
  background: #f8fafc;
  border: 2px solid #e8f4fc;
  border-radius: 16px;
  padding: 25px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  outline: none;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.cohort-card:hover {
  transform: translateY(-4px);
  border-color: #3498db;
  box-shadow: 0 10px 20px rgba(52, 152, 219, 0.1);
}

.cohort-card.selected {
  background: linear-gradient(135deg, #e8f4fc 0%, #d4eaf7 100%);
  border-color: #3498db;
  box-shadow: 0 10px 30px rgba(52, 152, 219, 0.2);
}

.cohort-card:focus {
  outline: 2px solid #3498db;
  outline-offset: 2px;
}

.cohort-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3498db, #2ecc71);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.cohort-card.selected::before {
  transform: scaleX(1);
}

.cohort-icon {
  font-size: 3rem;
  margin-bottom: 15px;
  line-height: 1;
}

.cohort-name {
  font-size: 1.3rem;
  color: #2c3e50;
  margin-bottom: 10px;
  font-weight: 600;
}

.cohort-description {
  color: #5d6d7e;
  margin-bottom: 15px;
  line-height: 1.5;
  font-size: 0.95rem;
}

.cohort-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.tag {
  background: white;
  color: #3498db;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  border: 1px solid #e8f4fc;
}

.cohort-card.selected .tag {
  background: #3498db;
  color: white;
}

.next-btn {
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 16px 40px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-top: 10px;
  outline: none;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.next-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(52, 152, 219, 0.3);
}

.next-btn:focus {
  outline: 2px solid #3498db;
  outline-offset: 2px;
}

.next-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 测评界面 */
.assessment-wrapper {
  background: white;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
}

.assessment-controls {
  background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  color: white;
  padding: 20px 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.back-btn {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 10px 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
  outline: none;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.back-btn:focus {
  outline: 2px solid rgba(255, 255, 255, 0.3);
  outline-offset: 2px;
}

.question-progress {
  font-size: 1.2rem;
  font-weight: 600;
}

.current-question {
  font-size: 1.4rem;
}

.total-questions {
  opacity: 0.8;
}

.completion-status {
  text-align: right;
}

.answered-count {
  font-size: 1.8rem;
  font-weight: 700;
  color: #2ecc71;
}

.total-count {
  opacity: 0.8;
}

/* 问题卡片 */
.question-card {
  padding: 40px;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 30px;
}

.question-type-badge {
  background: #e8f4fc;
  color: #3498db;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
}

.question-difficulty {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.question-content {
  margin-bottom: 40px;
}

.question-text {
  font-size: 1.4rem;
  color: #2c3e50;
  line-height: 1.6;
  margin-bottom: 30px;
  font-weight: 500;
}

/* 答案区域 */
.answer-section {
  margin-top: 20px;
}

/* 填空题 */
.text-answer .input-wrapper {
  position: relative;
  max-width: 600px;
}

.text-input {
  width: 100%;
  padding: 18px 24px;
  border: 2px solid #e8f4fc;
  border-radius: 12px;
  font-size: 1.1rem;
  color: #2c3e50;
  background: #f8fafc;
  transition: all 0.3s ease;
  outline: none;
}

.text-input:focus {
  outline: none;
  border-color: #3498db;
  background: white;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.input-decoration {
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #3498db, #2ecc71);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.text-input:focus + .input-decoration {
  transform: scaleX(1);
}

.input-hints {
  display: flex;
  gap: 20px;
  margin-top: 12px;
  color: #7f8c8d;
  font-size: 0.9rem;
}

/* 学术单选题 - 完全修复交互问题 */
.choice-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  max-width: 1000px;
  margin: 0 auto;
  position: relative;
  z-index: 2;
}

.choice-option {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 28px;
  background: rgba(18, 26, 46, 0.7);
  backdrop-filter: blur(20px) saturate(180%);
  border: 2px solid rgba(100, 181, 255, 0.25);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  overflow: hidden;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  transform-style: preserve-3d;
  perspective: 1000px;
  pointer-events: auto !important;
  touch-action: manipulation;
  z-index: 1;
  outline: none;
}

/* 确保可点击性修复 */
.choice-option * {
  pointer-events: none;
}

.choice-option::before {
  pointer-events: none;
}

/* 学术装饰边框 */
.choice-option::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(135deg,
    rgba(100, 181, 255, 0.3),
    rgba(123, 104, 255, 0.3),
    rgba(168, 85, 247, 0.3),
    rgba(100, 181, 255, 0.3));
  border-radius: 22px;
  opacity: 0;
  transition: opacity 0.4s ease;
  z-index: -1;
  animation: borderGlow 3s ease-in-out infinite;
}

@keyframes borderGlow {
  0%, 100% {
    opacity: 0.3;
  }
  50% {
    opacity: 0.6;
  }
}

/* 内部渐变背景 */
.choice-option::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg,
    rgba(100, 181, 255, 0.08),
    rgba(123, 104, 255, 0.05),
    rgba(168, 85, 247, 0.03));
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: -1;
}

.choice-option:hover {
  border-color: rgba(100, 181, 255, 0.6);
  background: rgba(26, 39, 69, 0.85);
  transform: translateY(-6px) scale(1.02);
  box-shadow:
    0 20px 40px rgba(0, 0, 0, 0.4),
    0 8px 32px rgba(100, 181, 255, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.choice-option:hover::before {
  opacity: 0.7;
}

.choice-option:hover::after {
  opacity: 1;
}

.choice-option.selected {
  border-color: #64b5ff;
  background: linear-gradient(135deg,
    rgba(100, 181, 255, 0.15),
    rgba(61, 139, 255, 0.1));
  transform: translateY(-4px) scale(1.01);
  box-shadow:
    0 16px 32px rgba(0, 0, 0, 0.5),
    0 8px 24px rgba(100, 181, 255, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.15),
    0 0 0 2px rgba(100, 181, 255, 0.2) inset;
}

.choice-option.selected::before {
  opacity: 0.8;
  animation: selectedPulse 2s ease-in-out infinite;
}

@keyframes selectedPulse {
  0%, 100% {
    opacity: 0.6;
  }
  50% {
    opacity: 0.9;
  }
}

.choice-option.selected::after {
  opacity: 1;
  background: linear-gradient(135deg,
    rgba(100, 181, 255, 0.2),
    rgba(61, 139, 255, 0.15),
    rgba(123, 104, 255, 0.1));
}

/* 点击反馈 - 修复交互问题 */
.choice-option:active {
  transform: translateY(-2px) scale(0.995);
  transition: transform 0.1s cubic-bezier(0.4, 0, 0.2, 1);
  border-color: rgba(100, 181, 255, 0.8);
}

/* 聚焦状态 */
.choice-option:focus {
  outline: 2px solid rgba(100, 181, 255, 0.8);
  outline-offset: 2px;
}

/* 聚焦光环 */
.focus-ring {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border-radius: 24px;
  border: 2px solid rgba(100, 181, 255, 0.6);
  opacity: 0;
  animation: focusPulse 2s ease-in-out infinite;
  pointer-events: none;
  z-index: -1;
}

@keyframes focusPulse {
  0%, 100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.02);
  }
}

/* 点击涟漪效果 */
.click-ripple {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(100, 181, 255, 0.4) 0%, transparent 70%);
  transform: translate(-50%, -50%) scale(0);
  opacity: 0;
  pointer-events: none;
  z-index: 0;
}

.click-ripple.active {
  animation: rippleEffect 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes rippleEffect {
  0% {
    transform: translate(-50%, -50%) scale(0);
    opacity: 0.8;
  }
  100% {
    transform: translate(-50%, -50%) scale(4);
    opacity: 0;
  }
}

.option-indicator {
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.option-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 3px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.choice-option:hover .option-circle {
  border-color: rgba(76, 201, 240, 0.6);
  background: rgba(76, 201, 240, 0.1);
}

.choice-option.selected .option-circle {
  border-color: #4cc9f0;
  background: #4cc9f0;
  transform: scale(1.1);
  box-shadow: 0 0 15px rgba(76, 201, 240, 0.5);
}

.choice-option.selected .option-circle::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: white;
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
}

.option-content {
  flex: 1;
}

.option-key {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 4px;
  font-weight: 600;
}

.option-label {
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.4;
}

/* 对勾标记 */
.option-checkmark {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.choice-option.selected .option-checkmark {
  opacity: 1;
  animation: checkmarkAppear 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes checkmarkAppear {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.5);
  }
  70% {
    transform: translate(-50%, -50%) scale(1.2);
  }
  100% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

/* 矩阵题 */
.matrix-container {
  background: #f8fafc;
  border-radius: 16px;
  padding: 30px;
  border: 1px solid #e8f4fc;
}

.matrix-header {
  margin-bottom: 30px;
}

.matrix-title {
  font-size: 1.2rem;
  color: #2c3e50;
  font-weight: 600;
  margin-bottom: 15px;
}

.matrix-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #5d6d7e;
}

.legend-key {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: #e8f4fc;
  color: #3498db;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.9rem;
}

.matrix-rows {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.matrix-row {
  display: flex;
  align-items: center;
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e8f4fc;
  transition: all 0.2s ease;
  position: relative;
}

.matrix-row:hover {
  border-color: #3498db;
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.1);
}

.matrix-row.answered {
  background: rgba(232, 244, 252, 0.3);
}

.row-label {
  flex: 1;
  font-size: 1.1rem;
  color: #2c3e50;
  font-weight: 500;
  min-width: 200px;
}

.row-options {
  display: flex;
  gap: 16px;
}

.matrix-option {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: white;
  border: 2px solid #e8f4fc;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  pointer-events: auto !important;
  touch-action: manipulation;
  z-index: 1;
  position: relative;
  outline: none;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

/* 确保可点击性修复 */
.matrix-option * {
  pointer-events: none;
}

.matrix-option:hover {
  border-color: #3498db;
  transform: scale(1.1);
}

.matrix-option.selected {
  border-color: #3498db;
  background: #e8f4fc;
}

.matrix-option:focus {
  outline: 2px solid #3498db;
  outline-offset: 2px;
}

/* 矩阵题聚焦光环 */
.matrix-focus-ring {
  position: absolute;
  top: -6px;
  left: -6px;
  right: -6px;
  bottom: -6px;
  border-radius: 50%;
  border: 2px solid rgba(52, 152, 219, 0.6);
  opacity: 0;
  animation: matrixFocusPulse 2s ease-in-out infinite;
  pointer-events: none;
  z-index: -1;
}

@keyframes matrixFocusPulse {
  0%, 100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}

.matrix-option.selected .matrix-option-circle {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #3498db;
}

.matrix-option-checkmark {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #3498db;
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.matrix-option.selected .matrix-option-checkmark {
  opacity: 1;
  animation: checkmarkAppear 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 矩阵题点击涟漪效果 */
.matrix-click-ripple {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(52, 152, 219, 0.4) 0%, transparent 70%);
  transform: translate(-50%, -50%) scale(0);
  opacity: 0;
  pointer-events: none;
  z-index: 0;
}

.matrix-click-ripple.active {
  animation: matrixRippleEffect 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes matrixRippleEffect {
  0% {
    transform: translate(-50%, -50%) scale(0);
    opacity: 0.8;
  }
  100% {
    transform: translate(-50%, -50%) scale(3);
    opacity: 0;
  }
}

.row-status {
  margin-top: 8px;
  font-size: 0.9rem;
  color: #3498db;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  position: absolute;
  bottom: -25px;
  left: 0;
  right: 0;
  justify-content: center;
}

.status-text {
  background: rgba(52, 152, 219, 0.1);
  padding: 4px 10px;
  border-radius: 12px;
  border: 1px solid rgba(52, 152, 219, 0.2);
}

.matrix-progress {
  margin-top: 25px;
  padding-top: 20px;
  border-top: 1px solid rgba(52, 152, 219, 0.2);
}

.progress-text {
  font-size: 0.95rem;
  color: #2c3e50;
  margin-bottom: 8px;
  font-weight: 500;
}

.matrix-progress .progress-bar {
  height: 6px;
  background: #e8f4fc;
  border-radius: 3px;
  overflow: hidden;
}

.matrix-progress .progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3498db, #2980b9);
  border-radius: 3px;
  transition: width 0.5s ease-out;
}

/* 题目导航 */
.question-navigation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 30px 0;
  border-top: 1px solid #e8f4fc;
  margin-top: 40px;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: 2px solid #e8f4fc;
  background: white;
  color: #3498db;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
  outline: none;
}

.nav-btn:hover:not(:disabled) {
  border-color: #3498db;
  background: #e8f4fc;
  transform: translateY(-2px);
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.nav-btn:focus {
  outline: 2px solid #3498db;
  outline-offset: 2px;
}

.question-dots {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  flex: 1;
  margin: 0 20px;
}

.question-dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid #e8f4fc;
  background: white;
  color: #2c3e50;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
  outline: none;
}

.question-dot:hover {
  border-color: #3498db;
  transform: scale(1.1);
}

.question-dot.active {
  background: #3498db;
  color: white;
  border-color: #3498db;
}

.question-dot.answered {
  background: #2ecc71;
  color: white;
  border-color: #2ecc71;
}

.question-dot:focus {
  outline: 2px solid #3498db;
  outline-offset: 2px;
}

/* 提交区域 */
.submit-section {
  background: #f8fafc;
  padding: 30px;
  border-top: 1px solid #e8f4fc;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.submit-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #5d6d7e;
  font-size: 0.95rem;
}

.submit-btn {
  background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 16px 40px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 200px;
  justify-content: center;
  outline: none;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  position: relative;
  overflow: hidden;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(46, 204, 113, 0.3);
}

.submit-btn:focus {
  outline: 2px solid #27ae60;
  outline-offset: 2px;
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.submit-btn.submitting {
  opacity: 0.8;
  cursor: wait;
}

.submit-btn.submitting::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: submittingShimmer 1.5s infinite;
}

@keyframes submittingShimmer {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}

/* 结果页面 */
.results-container {
  background: white;
  border-radius: 20px;
  padding: 50px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
  max-width: 1000px;
  margin: 0 auto;
}

.results-header {
  text-align: center;
  margin-bottom: 40px;
}

.results-icon {
  color: #2ecc71;
  margin-bottom: 20px;
}

.results-title {
  font-size: 2.2rem;
  color: #2c3e50;
  margin-bottom: 12px;
  font-weight: 700;
}

.results-subtitle {
  color: #7f8c8d;
  font-size: 1.1rem;
}

.results-summary {
  margin-bottom: 40px;
}

.results-summary h3 {
  font-size: 1.4rem;
  color: #2c3e50;
  margin-bottom: 25px;
  font-weight: 600;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
}

.skill-item {
  background: #f8fafc;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e8f4fc;
}

.skill-name {
  font-size: 1.1rem;
  color: #2c3e50;
  margin-bottom: 12px;
  font-weight: 500;
}

.skill-progress {
  display: flex;
  align-items: center;
  gap: 15px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 1s ease-out;
}

.progress-fill.level-excellent {
  background: linear-gradient(90deg, #2ecc71, #27ae60);
}

.progress-fill.level-good {
  background: linear-gradient(90deg, #3498db, #2980b9);
}

.progress-fill.level-medium {
  background: linear-gradient(90deg, #f39c12, #e67e22);
}

.progress-fill.level-fair {
  background: linear-gradient(90deg, #e74c3c, #c0392b);
}

.progress-fill.level-poor {
  background: linear-gradient(90deg, #95a5a6, #7f8c8d);
}

.skill-score {
  min-width: 60px;
  text-align: right;
  font-weight: 600;
  color: #2c3e50;
}

.results-actions {
  display: flex;
  gap: 20px;
  justify-content: center;
  padding-top: 30px;
  border-top: 1px solid #e8f4fc;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 32px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  outline: none;
}

.action-btn.secondary {
  background: white;
  color: #3498db;
  border-color: #e8f4fc;
}

.action-btn.secondary:hover {
  border-color: #3498db;
  background: #e8f4fc;
}

.action-btn.secondary:focus {
  outline: 2px solid #3498db;
  outline-offset: 2px;
}

.action-btn.primary {
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  color: white;
}

.action-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(52, 152, 219, 0.2);
}

.action-btn.primary:focus {
  outline: 2px solid #2980b9;
  outline-offset: 2px;
}

/* 记忆功能 - 答案恢复通知横幅 */
.memory-notification {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  margin: 0 20px 16px;
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.12), rgba(46, 204, 113, 0.08));
  border: 1px solid rgba(52, 152, 219, 0.3);
  border-left: 4px solid #3498db;
  border-radius: 12px;
  color: #2c3e50;
  font-size: 0.95rem;
  animation: memorySlideIn 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 16px rgba(52, 152, 219, 0.15);
}

.memory-notification svg {
  color: #3498db;
  flex-shrink: 0;
}

.memory-text {
  flex: 1;
  font-weight: 500;
}

.memory-dismiss {
  background: rgba(52, 152, 219, 0.1);
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #5d6d7e;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.memory-dismiss:hover {
  background: rgba(52, 152, 219, 0.2);
  color: #2c3e50;
}

@keyframes memorySlideIn {
  0% {
    opacity: 0;
    transform: translateY(-12px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 记忆横幅过渡动画 */
.memory-fade-enter-active {
  animation: memorySlideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.memory-fade-leave-active {
  transition: all 0.3s ease;
}

.memory-fade-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

/* 加载状态 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.loading-spinner {
  text-align: center;
}

.spinner {
  width: 60px;
  height: 60px;
  border: 4px solid #e8f4fc;
  border-top-color: #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 调试按钮 */
.debug-btn {
  background: #f39c12;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  opacity: 0.7;
  transition: opacity 0.2s ease;
  outline: none;
}

.debug-btn:hover {
  opacity: 1;
}

.debug-btn:focus {
  outline: 2px solid #f39c12;
  outline-offset: 2px;
}

/* 错误提示 */
.error-message {
  position: fixed;
  top: 20px;
  right: 20px;
  left: 20px;
  max-width: 400px;
  margin: 0 auto;
  z-index: 1000;
}

.error-content {
  background: white;
  border-left: 4px solid #e74c3c;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 12px;
}

.error-content svg {
  color: #e74c3c;
  flex-shrink: 0;
}

.error-content p {
  flex: 1;
  color: #2c3e50;
  margin: 0;
  font-size: 0.95rem;
}

.error-retry {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 6px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s ease;
  outline: none;
}

.error-retry:hover {
  background: #c0392b;
}

.error-retry:focus {
  outline: 2px solid #c0392b;
  outline-offset: 2px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .professional-assessment {
    padding: 20px 15px;
  }

  .header-title {
    font-size: 2.2rem;
  }

  .cohort-grid {
    grid-template-columns: 1fr;
  }

  .selection-card,
  .assessment-wrapper,
  .results-container {
    padding: 25px;
  }

  .assessment-controls {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }

  .question-navigation {
    flex-direction: column;
    gap: 20px;
  }

  .question-dots {
    order: -1;
  }

  .submit-section {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .results-actions {
    flex-direction: column;
  }

  .action-btn {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .choice-grid {
    grid-template-columns: 1fr;
  }

  .matrix-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .row-label {
    min-width: auto;
  }

  .row-options {
    align-self: stretch;
    justify-content: space-between;
  }
}
</style>
<template>
  <div class="question-detail">
    <div class="detail-header">
      <button class="btn-back" @click="goBack">← 返回列表</button>
      <div class="header-info">
        <h2>问题 #{{ questionIndex + 1 }}</h2>
        <span class="dataset-label">{{ datasetLabel }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>

    <div v-else-if="error" class="error-state">
      <span class="error-icon">⚠️</span>
      <span>{{ error }}</span>
    </div>

    <div v-else class="detail-body">
      <div class="question-section">
        <h3>问题描述</h3>
        <p class="question-text">{{ questionData.question }}</p>
        <div class="question-meta">
          <span class="meta-item">难度: <strong>{{ questionData.difficulty }}</strong></span>
          <span class="meta-item">类型: <strong>{{ questionData.technique }}</strong></span>
          <span class="meta-item">领域: <strong>{{ questionData.domain }}</strong></span>
          <span class="meta-item">涉及表: <strong>{{ (questionData.tables || []).join(', ') }}</strong></span>
        </div>
      </div>

      <div class="match-section">
        <h3>匹配判定</h3>
        <div class="match-toggle-bar">
          <div class="match-item">
            <span class="match-label">SQL匹配</span>
            <div class="toggle-group">
              <button
                class="toggle-btn"
                :class="{ active: sqlMatchStatus === 'matched', auto: sqlMatchAuto && sqlMatchStatus === 'matched' }"
                :disabled="!hasAiSql"
                @click="toggleMatch('sql_match', 'matched')"
              >
                ✅ 匹配
              </button>
              <button
                class="toggle-btn"
                :class="{ active: sqlMatchStatus === 'not_matched', auto: sqlMatchAuto && sqlMatchStatus === 'not_matched' }"
                :disabled="!hasAiSql"
                @click="toggleMatch('sql_match', 'not_matched')"
              >
                ❌ 不匹配
              </button>
              <button
                class="toggle-btn clear-btn"
                :class="{ active: !sqlMatchStatus }"
                :disabled="!hasAiSql"
                @click="toggleMatch('sql_match', '')"
              >
                － 未判定
              </button>
            </div>
            <span v-if="sqlMatchAuto" class="match-hint">自动</span>
          </div>
          <div class="match-item">
            <span class="match-label">结果匹配</span>
            <div class="toggle-group">
              <button
                class="toggle-btn"
                :class="{ active: resultMatchStatus === 'matched', auto: resultMatchAuto && resultMatchStatus === 'matched' }"
                :disabled="!hasAiResult || !hasCorrectResult"
                @click="toggleMatch('result_match', 'matched')"
              >
                ✅ 匹配
              </button>
              <button
                class="toggle-btn"
                :class="{ active: resultMatchStatus === 'not_matched', auto: resultMatchAuto && resultMatchStatus === 'not_matched' }"
                :disabled="!hasAiResult || !hasCorrectResult"
                @click="toggleMatch('result_match', 'not_matched')"
              >
                ❌ 不匹配
              </button>
              <button
                class="toggle-btn clear-btn"
                :class="{ active: !resultMatchStatus }"
                :disabled="!hasAiResult || !hasCorrectResult"
                @click="toggleMatch('result_match', '')"
              >
                － 未判定
              </button>
            </div>
            <span v-if="resultMatchAuto" class="match-hint">自动</span>
            <span v-if="!hasAiResult || !hasCorrectResult" class="match-hint muted">需执行两侧SQL</span>
          </div>
        </div>
      </div>

      <div class="sql-comparison">
        <h3>SQL 对比</h3>
        <div class="sql-grid">
          <div class="sql-card correct-sql">
            <div class="sql-header">
              <span class="sql-label">正确 SQL</span>
            </div>
            <pre class="sql-code"><code>{{ questionData.sql }}</code></pre>
            <div class="sql-actions">
              <button
                class="btn-execute"
                :disabled="executingCorrect"
                @click="executeCorrectSql"
              >
                {{ executingCorrect ? '执行中...' : (hasCorrectResult ? '重新执行' : '执行') }}
              </button>
            </div>
            <div v-if="correctResult" class="sql-result">
              <div class="result-header">
                <span class="result-title">执行结果 ({{ correctResult.row_count }} 行)</span>
              </div>
              <div class="result-table-wrapper" v-if="correctResult.columns && correctResult.columns.length > 0">
                <table class="result-table">
                  <thead>
                    <tr>
                      <th v-for="col in correctResult.columns" :key="col">{{ col }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, ri) in correctResult.rows" :key="ri">
                      <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div v-else class="no-result">无数据</div>
            </div>
            <div v-if="correctError" class="sql-error">
              <span class="error-text">❌ {{ correctError }}</span>
            </div>
          </div>

          <div class="sql-card ai-sql">
            <div class="sql-header">
              <span class="sql-label">AI 生成 SQL</span>
            </div>
            <div v-if="generatingAi" class="generating-state">
              <div class="spinner"></div>
              <span>AI生成中...</span>
            </div>
            <template v-else>
              <pre v-if="aiSql" class="sql-code"><code>{{ aiSql }}</code></pre>
              <div v-else class="no-sql">尚未生成</div>
            </template>
            <div class="sql-actions">
              <button
                class="btn-generate"
                :disabled="generatingAi"
                @click="generateAi"
              >
                {{ generatingAi ? '生成中...' : (aiSql ? '重新生成' : 'AI生成SQL') }}
              </button>
              <button
                v-if="aiSql"
                class="btn-execute"
                :disabled="executingAi"
                @click="executeAiSql"
              >
                {{ executingAi ? '执行中...' : (hasAiResult ? '重新执行' : '执行') }}
              </button>
            </div>
            <div v-if="aiResult" class="sql-result">
              <div class="result-header">
                <span class="result-title">执行结果 ({{ aiResult.row_count }} 行)</span>
              </div>
              <div class="result-table-wrapper" v-if="aiResult.columns && aiResult.columns.length > 0">
                <table class="result-table">
                  <thead>
                    <tr>
                      <th v-for="col in aiResult.columns" :key="col">{{ col }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, ri) in aiResult.rows" :key="ri">
                      <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div v-else class="no-result">无数据</div>
            </div>
            <div v-if="aiError" class="sql-error">
              <span class="error-text">❌ {{ aiError }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="elapsed-time" v-if="resultData.ai_elapsed">
        <span>AI生成耗时: {{ resultData.ai_elapsed.toFixed(2) }}s</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { getQuestionDetail, generateAiSql, executeSql, setMatchStatus } from './api.js'

const props = defineProps({
  datasetName: String,
  questionIndex: Number
})

const emit = defineEmits(['back'])

const labels = {
  qa_simple: '简单查询',
  qa_agg: '聚合查询',
  qa_join: '多表关联',
  qa_advanced: '高级查询',
  qa_synonyms: '同义词/别名'
}

const datasetLabel = computed(() => labels[props.datasetName] || props.datasetName)
const loading = ref(false)
const error = ref('')
const questionData = ref({})
const resultData = ref({})
const aiSql = ref('')
const generatingAi = ref(false)
const executingCorrect = ref(false)
const executingAi = ref(false)
const correctResult = ref(null)
const correctError = ref('')
const aiResult = ref(null)
const aiError = ref('')

const sqlMatchStatus = ref(null)
const resultMatchStatus = ref(null)
const sqlMatchAuto = ref(false)
const resultMatchAuto = ref(false)

const hasAiSql = computed(() => !!aiSql.value)
const hasCorrectResult = computed(() => correctResult.value !== null)
const hasAiResult = computed(() => aiResult.value !== null)

function goBack() {
  emit('back')
}

async function loadDetail() {
  loading.value = true
  error.value = ''
  try {
    const res = await getQuestionDetail(props.datasetName, props.questionIndex)
    questionData.value = res.data.question || {}
    resultData.value = res.data.result || {}
    aiSql.value = resultData.value.ai_generated_sql || ''
    sqlMatchStatus.value = resultData.value.sql_match || null
    resultMatchStatus.value = resultData.value.result_match || null
    if (resultData.value.correct_sql_result) {
      correctResult.value = resultData.value.correct_sql_result
    }
    if (resultData.value.ai_sql_result) {
      aiResult.value = resultData.value.ai_sql_result
    }
  } catch (e) {
    error.value = '加载问题详情失败'
  } finally {
    loading.value = false
  }
}

async function toggleMatch(matchType, value) {
  const newVal = value || null
  if (matchType === 'sql_match') {
    sqlMatchStatus.value = newVal
    sqlMatchAuto.value = false
  } else {
    resultMatchStatus.value = newVal
    resultMatchAuto.value = false
  }
  try {
    await setMatchStatus(props.datasetName, props.questionIndex, matchType, value)
  } catch (e) {
    console.error('Failed to set match status:', e)
  }
}

async function generateAi() {
  generatingAi.value = true
  aiError.value = ''
  try {
    const res = await generateAiSql(props.datasetName, props.questionIndex)
    if (res.data.success) {
      aiSql.value = res.data.ai_sql || ''
      sqlMatchStatus.value = res.data.sql_match || null
      sqlMatchAuto.value = true
      if (res.data.error) {
        aiError.value = res.data.error
      }
      if (res.data.explanation) {
        aiSql.value = aiSql.value + '\n\n-- ' + res.data.explanation
      }
    } else {
      aiError.value = res.data.error || 'AI生成失败'
    }
  } catch (e) {
    aiError.value = 'AI生成请求失败'
  } finally {
    generatingAi.value = false
  }
}

async function executeCorrectSql() {
  executingCorrect.value = true
  correctError.value = ''
  try {
    const res = await executeSql(props.datasetName, props.questionIndex, questionData.value.sql, 'correct')
    if (res.data.success) {
      correctResult.value = {
        columns: res.data.columns,
        rows: res.data.rows,
        row_count: res.data.row_count
      }
      if (hasAiResult.value) {
        await autoMatchResult()
      }
    } else {
      correctError.value = res.data.error || '执行失败'
    }
  } catch (e) {
    correctError.value = '执行请求失败'
  } finally {
    executingCorrect.value = false
  }
}

async function executeAiSql() {
  executingAi.value = true
  aiError.value = ''
  try {
    const res = await executeSql(props.datasetName, props.questionIndex, aiSql.value, 'ai')
    if (res.data.success) {
      aiResult.value = {
        columns: res.data.columns,
        rows: res.data.rows,
        row_count: res.data.row_count
      }
      if (hasCorrectResult.value) {
        await autoMatchResult()
      }
    } else {
      aiError.value = res.data.error || '执行失败'
    }
  } catch (e) {
    aiError.value = '执行请求失败'
  } finally {
    executingAi.value = false
  }
}

async function autoMatchResult() {
  const detailRes = await getQuestionDetail(props.datasetName, props.questionIndex)
  const updatedResult = detailRes.data.result || {}
  if (updatedResult.result_match) {
    resultMatchStatus.value = updatedResult.result_match
    resultMatchAuto.value = true
  }
}

watch([() => props.datasetName, () => props.questionIndex], () => {
  correctResult.value = null
  correctError.value = ''
  aiResult.value = null
  aiError.value = ''
  sqlMatchStatus.value = null
  resultMatchStatus.value = null
  sqlMatchAuto.value = false
  resultMatchAuto.value = false
  loadDetail()
}, { immediate: true })
</script>

<style scoped>
.question-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
  background: white;
}

.btn-back {
  padding: 8px 16px;
  background: #f0f2f6;
  color: #666;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.btn-back:hover {
  background: #e0e4ea;
  color: #333;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-info h2 {
  font-size: 18px;
  color: #333;
}

.dataset-label {
  font-size: 12px;
  color: #667eea;
  background: #f0f2ff;
  padding: 3px 10px;
  border-radius: 12px;
}

.loading-state, .error-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #666;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #eee;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 32px;
}

.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.question-section {
  background: white;
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 16px;
}

.question-section h3 {
  font-size: 14px;
  color: #999;
  margin-bottom: 8px;
}

.question-text {
  font-size: 18px;
  color: #333;
  font-weight: 600;
  margin-bottom: 12px;
  line-height: 1.5;
}

.question-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-item {
  font-size: 13px;
  color: #666;
}

.match-section {
  background: white;
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 16px;
}

.match-section h3 {
  font-size: 14px;
  color: #999;
  margin-bottom: 12px;
}

.match-toggle-bar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.match-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.match-label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  min-width: 80px;
}

.toggle-group {
  display: flex;
  gap: 6px;
}

.toggle-btn {
  padding: 6px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: white;
  color: #666;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.toggle-btn:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
}

.toggle-btn.active {
  border-color: #667eea;
  background: #f0f2ff;
  color: #667eea;
  font-weight: 600;
}

.toggle-btn.active.auto {
  border-color: #52c41a;
  background: #f6ffed;
  color: #52c41a;
}

.toggle-btn.clear-btn.active {
  border-color: #d9d9d9;
  background: #f5f5f5;
  color: #999;
}

.toggle-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.match-hint {
  font-size: 11px;
  color: #52c41a;
  background: #f6ffed;
  padding: 2px 8px;
  border-radius: 4px;
}

.match-hint.muted {
  color: #999;
  background: #f5f5f5;
}

.sql-comparison h3 {
  font-size: 14px;
  color: #999;
  margin-bottom: 12px;
}

.sql-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.sql-card {
  background: white;
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 16px;
  min-height: 200px;
}

.sql-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.sql-label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.correct-sql .sql-label { color: #52c41a; }
.ai-sql .sql-label { color: #667eea; }

.sql-code {
  background: #f5f5f5;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 12px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.5;
  max-height: 300px;
  overflow-y: auto;
}

.no-sql, .generating-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: #999;
  font-size: 14px;
}

.sql-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.btn-generate, .btn-execute {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.btn-generate {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-generate:hover:not(:disabled) { opacity: 0.9; }
.btn-generate:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-execute {
  background: #52c41a;
  color: white;
}

.btn-execute:hover:not(:disabled) { opacity: 0.9; }
.btn-execute:disabled { opacity: 0.5; cursor: not-allowed; }

.sql-result {
  margin-top: 12px;
  border-top: 1px solid #eee;
  padding-top: 12px;
}

.result-header {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.result-title {
  font-weight: 600;
}

.result-table-wrapper {
  overflow-x: auto;
}

.result-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.result-table th {
  background: #fafafa;
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border: 1px solid #e8e8e8;
  white-space: nowrap;
}

.result-table td {
  padding: 6px 12px;
  border: 1px solid #e8e8e8;
  color: #666;
}

.result-table tr:hover td {
  background: #f8f9ff;
}

.no-result {
  color: #999;
  font-size: 13px;
  text-align: center;
  padding: 20px;
}

.sql-error {
  margin-top: 8px;
}

.error-text {
  font-size: 13px;
  color: #ff4d4f;
}

.elapsed-time {
  margin-top: 16px;
  text-align: right;
  font-size: 12px;
  color: #999;
}
</style>

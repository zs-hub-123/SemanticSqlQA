<template>
  <div class="question-list">
    <div class="list-header">
      <div class="header-left">
        <h2>{{ datasetLabel }}</h2>
        <span class="question-count">共 {{ totalCount }} 题</span>
      </div>
      <div class="header-right">
        <div class="auto-test-controls" v-if="!autoTestRunning">
          <input
            class="interval-input"
            type="number"
            v-model.number="autoTestInterval"
            min="5"
            max="300"
            title="测试间隔(秒)"
          />
          <span class="interval-label">秒</span>
          <label class="skip-checkbox">
            <input type="checkbox" v-model="skipExisting" />
            <span>跳过已测试</span>
          </label>
          <button
            class="btn-auto-test"
            :disabled="autoTestStarting"
            @click="startAutoTest"
          >
            {{ autoTestStarting ? '启动中...' : '自动测试' }}
          </button>
        </div>
        <div class="auto-test-status" v-else>
          <span class="auto-test-info">
            {{ autoTestCompleted }}/{{ autoTestTotal }}
          </span>
          <button class="btn-stop-test" @click="stopAutoTest">停止</button>
        </div>
        <button
          class="btn-auto-match"
          :disabled="autoMatchRunning || autoTestRunning"
          @click="handleAutoMatch"
          title="对已生成的SQL和执行结果进行自动匹配"
        >
          {{ autoMatchRunning ? '匹配中...' : '自动匹配' }}
        </button>
        <span class="tested-count">{{ datasetStats.tested || 0 }} 已测试</span>
        <span class="accuracy" v-if="datasetStats.sql_accuracy > 0">SQL准确率: {{ datasetStats.sql_accuracy }}%</span>
        <span class="accuracy result" v-if="datasetStats.result_accuracy > 0">结果准确率: {{ datasetStats.result_accuracy }}%</span>
      </div>
    </div>

    <div class="auto-test-progress-bar" v-if="autoTestRunning">
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <div class="progress-info">
        <span>测试进度: {{ autoTestCompleted }}/{{ autoTestTotal }}</span>
        <span>当前: 第{{ autoTestPosition + 1 }}个 / 共{{ autoTestTotal }}题</span>
        <span>耗时: {{ autoTestElapsed }}s</span>
        <span class="error-count" v-if="autoTestErrors.length > 0">
          错误: {{ autoTestErrors.length }}
        </span>
      </div>
    </div>

    <div class="auto-match-result-bar" v-if="autoMatchResult">
      <div class="match-result-info">
        <span class="match-title">匹配完成</span>
        <span class="match-stat sql-matched">✅ SQL匹配成功: {{ autoMatchResult.sql_matched }}</span>
        <span class="match-stat sql-not-matched">❌ SQL未匹配: {{ autoMatchResult.sql_not_matched }}</span>
        <span class="match-divider">|</span>
        <span class="match-stat result-matched">📗 结果匹配: {{ autoMatchResult.result_matched }}</span>
        <span class="match-stat result-not-matched">📕 结果未匹配: {{ autoMatchResult.result_not_matched }}</span>
        <span class="match-divider">|</span>
        <span class="match-stat skipped">⏭️ 跳过(无AI结果): {{ autoMatchResult.skipped }}</span>
      </div>
      <button class="btn-close-result" @click="autoMatchResult = null">关闭</button>
    </div>

    <div class="pagination-bar">
      <button class="btn-page" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">上一页</button>
      <button
        v-for="p in visiblePages"
        :key="p"
        class="btn-page"
        :class="{ active: p === currentPage, ellipsis: p === '...' }"
        :disabled="p === '...'"
        @click="p !== '...' && goPage(p)"
      >{{ p }}</button>
      <button class="btn-page" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">下一页</button>
      <span class="page-info">{{ currentPage }}/{{ totalPages }}页 共{{ totalCount }}题</span>
    </div>

    <div class="list-stats-bar">
      <div class="stat-item">
        <span class="stat-label">已测试</span>
        <span class="stat-value">{{ datasetStats.tested || 0 }}/{{ datasetStats.total || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">SQL准确率</span>
        <span class="stat-value" :style="{color: (datasetStats.sql_accuracy || 0) >= 80 ? '#52c41a' : (datasetStats.sql_accuracy || 0) >= 50 ? '#faad14' : '#ff4d4f'}">{{ datasetStats.sql_accuracy || 0 }}%</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">结果准确率</span>
        <span class="stat-value" :style="{color: (datasetStats.result_accuracy || 0) >= 80 ? '#52c41a' : (datasetStats.result_accuracy || 0) >= 50 ? '#faad14' : '#ff4d4f'}">{{ datasetStats.result_accuracy || 0 }}%</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">正确SQL已执行</span>
        <span class="stat-value">{{ datasetStats.correct_executed || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">AI SQL已执行</span>
        <span class="stat-value">{{ datasetStats.ai_executed || 0 }}</span>
      </div>
    </div>

    <div class="list-body">
      <div
        v-for="q in questions"
        :key="q.index"
        class="question-card"
        :class="{
          'match-true': q.sql_match === 'matched',
          'match-false': q.sql_match === 'not_matched',
          'not-tested': !q.tested
        }"
        @click="openDetail(q.index)"
      >
        <div class="card-left">
          <span class="question-index">#{{ q.index + 1 }}</span>
        </div>
        <div class="card-content">
          <div class="question-text">{{ q.question }}</div>
          <div class="question-tags">
            <span class="tag difficulty" :class="q.difficulty">{{ q.difficulty }}</span>
            <span class="tag technique">{{ q.technique }}</span>
            <span class="tag domain">{{ q.domain }}</span>
          </div>
        </div>
        <div class="card-right">
          <div class="match-icons">
            <span v-if="q.tested" class="match-icon" title="SQL匹配">
              {{ q.sql_match === 'matched' ? '✅' : q.sql_match === 'not_matched' ? '❌' : '🔲' }}
            </span>
            <span v-if="q.result_match" class="match-icon" title="结果匹配">
              {{ q.result_match === 'matched' ? '📗' : '📕' }}
            </span>
            <span v-if="!q.tested" class="status-icon pending">⏳</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { getDatasetQuestions, startAutoTest as apiStartAutoTest, stopAutoTest as apiStopAutoTest, getAutoTestStatus, autoMatch } from './api.js'

const emit = defineEmits(['open-detail'])
const props = defineProps({
  datasetName: String,
  initialPage: { type: Number, default: 1 }
})

const questions = ref([])
const datasetLabel = ref('')
const datasetStats = ref({})
const autoTestRunning = ref(false)
const autoTestStarting = ref(false)
const autoTestTaskId = ref('')
const autoTestTotal = ref(0)
const autoTestCompleted = ref(0)
const autoTestPosition = ref(0)
const autoTestElapsed = ref(0)
const autoTestInterval = ref(30)
const skipExisting = ref(true)
const autoTestErrors = ref([])
const autoMatchRunning = ref(false)
const autoMatchResult = ref(null)
let statusPollTimer = null

const progressPercent = computed(() => {
  if (autoTestTotal.value === 0) return 0
  return Math.round(autoTestCompleted.value / autoTestTotal.value * 100)
})

const testedCount = computed(() => questions.value.filter(q => q.tested).length)
const correctExecutedCount = computed(() => questions.value.filter(q => q.correct_executed).length)
const aiExecutedCount = computed(() => questions.value.filter(q => q.ai_executed).length)

const currentPage = ref(1)
const totalPages = ref(1)
const totalCount = ref(0)
const pageSize = 10

const visiblePages = computed(() => {
  const tp = totalPages.value
  const cp = currentPage.value
  if (tp <= 7) return Array.from({ length: tp }, (_, i) => i + 1)
  const pages = []
  pages.push(1)
  if (cp > 3) pages.push('...')
  for (let p = Math.max(2, cp - 1); p <= Math.min(tp - 1, cp + 1); p++) pages.push(p)
  if (cp < tp - 2) pages.push('...')
  pages.push(tp)
  return pages
})

const sqlAccuracy = computed(() => {
  const tested = questions.value.filter(q => q.tested)
  if (tested.length === 0) return 0
  const matched = tested.filter(q => q.sql_match === 'matched').length
  return Math.round(matched / tested.length * 100)
})

const resultAccuracy = computed(() => {
  const withResult = questions.value.filter(q => q.result_match)
  if (withResult.length === 0) return 0
  const matched = withResult.filter(q => q.result_match === 'matched').length
  return Math.round(matched / withResult.length * 100)
})

function openDetail(index) {
  emit('open-detail', props.datasetName, index, currentPage.value)
}

async function startAutoTest() {
  autoTestStarting.value = true
  try {
    const res = await apiStartAutoTest(props.datasetName, autoTestInterval.value, skipExisting.value)
    if (res.data.success) {
      autoTestRunning.value = true
      autoTestTaskId.value = res.data.task_id
      autoTestTotal.value = res.data.total
      autoTestCompleted.value = 0
      autoTestPosition.value = 0
      autoTestElapsed.value = 0
      autoTestErrors.value = []
      startStatusPolling()
    } else {
      alert(res.data.error || '启动自动测试失败')
    }
  } catch (e) {
    alert('启动自动测试失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    autoTestStarting.value = false
  }
}

async function stopAutoTest() {
  try {
    await apiStopAutoTest(autoTestTaskId.value)
  } catch (e) {
    console.error('停止失败:', e)
  }
  autoTestRunning.value = false
  clearStatusPolling()
  refreshQuestions()
}

function startStatusPolling() {
  clearStatusPolling()
  statusPollTimer = setInterval(async () => {
    try {
      const res = await getAutoTestStatus(autoTestTaskId.value)
      if (res.data.success) {
        autoTestCompleted.value = res.data.completed
        autoTestPosition.value = res.data.position || 0
        autoTestElapsed.value = res.data.elapsed
        autoTestErrors.value = res.data.errors || []
        if (!res.data.running && res.data.completed >= res.data.total) {
          autoTestRunning.value = false
          clearStatusPolling()
          refreshQuestions()
        } else if (!res.data.running) {
          autoTestRunning.value = false
          clearStatusPolling()
          refreshQuestions()
        }
      }
    } catch (e) {
      console.error('状态查询失败:', e)
    }
  }, 2000)
}

function clearStatusPolling() {
  if (statusPollTimer) {
    clearInterval(statusPollTimer)
    statusPollTimer = null
  }
}

async function handleAutoMatch() {
  if (!confirm('确定要对当前数据集执行自动匹配吗？这将覆盖手动标记的结果。')) {
    return
  }
  autoMatchRunning.value = true
  autoMatchResult.value = null
  try {
    const res = await autoMatch(props.datasetName)
    if (res.data.success) {
      autoMatchResult.value = res.data
      refreshQuestions()
    } else {
      alert(res.data.error || '自动匹配失败')
    }
  } catch (e) {
    alert('自动匹配失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    autoMatchRunning.value = false
  }
}

async function refreshQuestions() {
  try {
    const res = await getDatasetQuestions(props.datasetName, currentPage.value, pageSize)
    questions.value = res.data.questions || []
  } catch (e) {
    console.error('刷新问题列表失败:', e)
  }
}

function goPage(p) {
  if (p < 1 || p > totalPages.value) return
  currentPage.value = p
  loadQuestions(props.datasetName, p)
}

async function loadQuestions(name, page = 1) {
  try {
    const res = await getDatasetQuestions(name, page, pageSize)
    questions.value = res.data.questions || []
    if (res.data.stats) datasetStats.value = res.data.stats
    if (res.data.pagination) {
      currentPage.value = res.data.pagination.page
      totalPages.value = res.data.pagination.total_pages
      totalCount.value = res.data.pagination.total
    }
  } catch (e) {
    console.error('Failed to load questions:', e)
    questions.value = []
  }
}

const labels = {
  qa_simple: '简单查询',
  qa_agg: '聚合查询',
  qa_join: '多表关联',
  qa_advanced: '高级查询',
  qa_synonyms: '同义词/别名'
}

watch(() => props.datasetName, async (name) => {
  if (!name) return
  autoTestRunning.value = false
  clearStatusPolling()
  currentPage.value = props.initialPage
  datasetLabel.value = labels[name] || name
  loadQuestions(name, props.initialPage)
}, { immediate: true })

onUnmounted(() => {
  clearStatusPolling()
  if (autoTestTaskId.value) {
    apiStopAutoTest(autoTestTaskId.value).catch(() => {})
  }
})
</script>

<style scoped>
.question-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
  background: white;
  flex-wrap: wrap;
  gap: 8px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  font-size: 20px;
  color: #333;
}

.question-count {
  font-size: 13px;
  color: #999;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: #666;
  flex-wrap: wrap;
}

.accuracy {
  color: #667eea;
  font-weight: 600;
}

.accuracy.result {
  color: #52c41a;
}

.auto-test-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.interval-input {
  width: 55px;
  padding: 4px 6px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
  text-align: center;
}

.interval-label {
  font-size: 12px;
  color: #999;
  margin-right: 4px;
}

.skip-checkbox {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  white-space: nowrap;
}

.skip-checkbox input {
  cursor: pointer;
}

.btn-auto-test {
  padding: 6px 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: opacity 0.2s;
  white-space: nowrap;
}

.btn-auto-test:hover:not(:disabled) { opacity: 0.9; }
.btn-auto-test:disabled { opacity: 0.5; cursor: not-allowed; }

.auto-test-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.auto-test-info {
  font-size: 13px;
  font-weight: 600;
  color: #667eea;
}

.btn-stop-test {
  padding: 6px 14px;
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: opacity 0.2s;
}

.btn-stop-test:hover { opacity: 0.9; }

.btn-auto-match {
  padding: 6px 14px;
  background: #52c41a;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: opacity 0.2s;
  white-space: nowrap;
}

.btn-auto-match:hover:not(:disabled) { opacity: 0.9; }
.btn-auto-match:disabled { opacity: 0.5; cursor: not-allowed; }

.auto-test-progress-bar {
  padding: 10px 24px;
  background: #f0f2ff;
  border-bottom: 1px solid #e0e4f0;
}

.auto-match-result-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 24px;
  background: #f6ffed;
  border-bottom: 1px solid #b7eb8f;
}

.match-result-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.match-title {
  font-weight: 600;
  color: #52c41a;
  font-size: 13px;
}

.match-stat {
  font-size: 12px;
}

.match-divider {
  color: #d9d9d9;
}

.sql-matched { color: #52c41a; }
.sql-not-matched { color: #ff4d4f; }
.result-matched { color: #52c41a; }
.result-not-matched { color: #ff4d4f; }
.skipped { color: #999; }

.btn-close-result {
  padding: 4px 12px;
  background: #fff;
  color: #666;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn-close-result:hover {
  border-color: #52c41a;
  color: #52c41a;
}

.progress-track {
  height: 6px;
  background: #e0e4f0;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 6px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 3px;
  transition: width 1s ease;
}

.progress-info {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #666;
}

.error-count {
  color: #ff4d4f;
  font-weight: 600;
}

.pagination-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px 24px;
  background: white;
  border-bottom: 1px solid #eee;
  flex-wrap: wrap;
}

.btn-page {
  min-width: 36px;
  height: 32px;
  padding: 0 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: white;
  color: #333;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-page:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
}

.btn-page.active {
  background: #667eea;
  border-color: #667eea;
  color: white;
  font-weight: 600;
}

.btn-page:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.btn-page.ellipsis {
  border: none;
  background: none;
  cursor: default;
  color: #999;
}

.page-info {
  margin-left: 8px;
  font-size: 13px;
  color: #999;
}

.list-stats-bar {
  display: flex;
  gap: 24px;
  padding: 12px 24px;
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-size: 11px;
  color: #999;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #333;
}

.list-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 24px;
}

.question-card {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  margin: 6px 0;
  background: white;
  border: 1px solid #eee;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.question-card:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
}

.question-card.match-true {
  border-left: 4px solid #52c41a;
}

.question-card.match-false {
  border-left: 4px solid #ff4d4f;
}

.question-card.not-tested {
  border-left: 4px solid #d9d9d9;
}

.card-left {
  margin-right: 16px;
}

.question-index {
  font-size: 13px;
  font-weight: 700;
  color: #667eea;
  background: #f0f2ff;
  padding: 4px 10px;
  border-radius: 6px;
}

.card-content {
  flex: 1;
}

.question-text {
  font-size: 15px;
  color: #333;
  margin-bottom: 6px;
  line-height: 1.4;
}

.question-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #f0f2f6;
  color: #666;
}

.tag.difficulty.easy { background: #f6ffed; color: #52c41a; }
.tag.difficulty.medium { background: #fffbe6; color: #faad14; }
.tag.difficulty.hard { background: #fff2f0; color: #ff4d4f; }

.card-right {
  margin-left: 12px;
}

.match-icons {
  display: flex;
  gap: 4px;
  align-items: center;
}

.match-icon {
  font-size: 16px;
}

.status-icon.pending {
  opacity: 0.4;
}
</style>

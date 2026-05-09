<template>
  <div class="stats-view">
    <div class="stats-header">
      <button class="btn-back" @click="$emit('back')">← 返回</button>
      <h2>数据统计</h2>
      <div class="header-actions">
        <ModelSelector @model-changed="onModelChanged" />
        <button class="btn-reset" @click="handleReset">初始化测试集</button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载统计中...</span>
    </div>

    <div v-else-if="resetLoading" class="loading-state">
      <div class="spinner"></div>
      <span>正在初始化...</span>
    </div>

    <div v-else class="stats-body">
      <div class="overall-stats">
        <h3>总体统计</h3>
        <div class="stats-grid">
          <div class="stat-card primary">
            <span class="stat-number">{{ overallStats.total_questions }}</span>
            <span class="stat-desc">总问题数</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ overallStats.total_datasets }}</span>
            <span class="stat-desc">数据集数量</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ overallStats.total_tested }}</span>
            <span class="stat-desc">已测试</span>
          </div>
          <div class="stat-card accent">
            <span class="stat-number" :style="{color: overallStats.overall_sql_generation_accuracy >= 80 ? '#52c41a' : overallStats.overall_sql_generation_accuracy >= 50 ? '#faad14' : '#ff4d4f'}">
              {{ overallStats.overall_sql_generation_accuracy }}%
            </span>
            <span class="stat-desc">SQL生成准确率</span>
          </div>
          <div class="stat-card accent">
            <span class="stat-number" :style="{color: overallStats.overall_sql_execution_accuracy >= 80 ? '#52c41a' : overallStats.overall_sql_execution_accuracy >= 50 ? '#faad14' : '#ff4d4f'}">
              {{ overallStats.overall_sql_execution_accuracy }}%
            </span>
            <span class="stat-desc">SQL执行结果准确率</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ overallStats.total_sql_match }}</span>
            <span class="stat-desc">SQL匹配成功</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ overallStats.total_result_match }}</span>
            <span class="stat-desc">结果匹配成功</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ overallStats.total_correct_executed }}</span>
            <span class="stat-desc">正确SQL已执行</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ overallStats.total_ai_executed }}</span>
            <span class="stat-desc">AI SQL已执行</span>
          </div>
        </div>
      </div>

      <div class="per-dataset-stats">
        <h3>各数据集统计</h3>
        <div class="stats-table-wrapper">
          <table class="stats-table">
            <thead>
              <tr>
                <th>数据集</th>
                <th>总题数</th>
                <th>已测试</th>
                <th>SQL生成准确率</th>
                <th>SQL执行结果准确率</th>
                <th>测试覆盖率</th>
                <th>正确SQL已执行</th>
                <th>AI SQL已执行</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(stats, name) in overallStats.per_dataset" :key="name">
                <td class="dataset-name-cell">{{ labels[name] || name }}</td>
                <td>{{ stats.total }}</td>
                <td>{{ stats.tested }}</td>
                <td>
                  <span class="accuracy-badge" :class="accuracyClass(stats.sql_generation_accuracy)">
                    {{ stats.sql_generation_accuracy }}%
                  </span>
                </td>
                <td>
                  <span class="accuracy-badge" :class="accuracyClass(stats.sql_execution_accuracy)">
                    {{ stats.sql_execution_accuracy }}%
                  </span>
                </td>
                <td>{{ stats.test_coverage }}%</td>
                <td>{{ stats.correct_executed }}</td>
                <td>{{ stats.ai_executed }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAllStats, resetTestResults } from './api.js'
import ModelSelector from '../components/ModelSelector.vue'

const emit = defineEmits(['back'])

function onModelChanged(modelInfo) {
  console.log('Model switched to:', modelInfo.current_model)
}

const labels = {
  qa_simple: '简单查询',
  qa_agg: '聚合查询',
  qa_join: '多表关联',
  qa_advanced: '高级查询',
  qa_synonyms: '同义词/别名'
}

const loading = ref(false)
const resetLoading = ref(false)
const overallStats = ref({
  total_questions: 0,
  total_datasets: 0,
  total_tested: 0,
  total_sql_match: 0,
  total_result_match: 0,
  total_result_set: 0,
  total_correct_executed: 0,
  total_ai_executed: 0,
  overall_sql_generation_accuracy: 0,
  overall_sql_execution_accuracy: 0,
  overall_result_accuracy: 0,
  per_dataset: {}
})

function accuracyClass(accuracy) {
  if (accuracy >= 80) return 'accuracy-high'
  if (accuracy >= 50) return 'accuracy-mid'
  return 'accuracy-low'
}

async function loadStats() {
  loading.value = true
  try {
    const res = await getAllStats()
    overallStats.value = res.data.stats || overallStats.value
  } catch (e) {
    console.error('Failed to load stats:', e)
  } finally {
    loading.value = false
  }
}

async function handleReset() {
  if (!confirm('确定要初始化测试集吗？这将清除所有测试结果。')) {
    return
  }
  resetLoading.value = true
  try {
    await resetTestResults()
    await loadStats()
    alert('测试集已初始化')
  } catch (e) {
    console.error('Failed to reset:', e)
    alert('初始化失败')
  } finally {
    resetLoading.value = false
  }
}

onMounted(loadStats)
</script>

<style scoped>
.stats-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.stats-header {
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
}

.btn-back:hover {
  background: #e0e4ea;
  color: #333;
}

.stats-header h2 {
  font-size: 20px;
  color: #333;
}

.header-actions {
  margin-left: auto;
}

.btn-reset {
  padding: 8px 16px;
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

.btn-reset:hover {
  background: #ff7875;
}

.loading-state {
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

.stats-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.overall-stats h3, .per-dataset-stats h3 {
  font-size: 16px;
  color: #333;
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.stat-card.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
}

.stat-card.accent {
  border-color: #667eea;
  background: #f8f9ff;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #333;
}

.stat-card.primary .stat-number {
  color: white;
}

.stat-desc {
  font-size: 13px;
  color: #999;
}

.stat-card.primary .stat-desc {
  color: rgba(255,255,255,0.8);
}

.stats-table-wrapper {
  overflow-x: auto;
}

.stats-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.stats-table th {
  background: #fafafa;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border: 1px solid #e8e8e8;
  white-space: nowrap;
}

.stats-table td {
  padding: 10px 16px;
  border: 1px solid #e8e8e8;
  color: #666;
}

.stats-table tbody tr:hover td {
  background: #f8f9ff;
}

.dataset-name-cell {
  font-weight: 600;
  color: #333 !important;
}

.accuracy-badge {
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 12px;
  display: inline-block;
}

.accuracy-high {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.accuracy-mid {
  background: #fffbe6;
  color: #faad14;
  border: 1px solid #ffe58f;
}

.accuracy-low {
  background: #fff2f0;
  color: #ff4d4f;
  border: 1px solid #ffccc7;
}
</style>

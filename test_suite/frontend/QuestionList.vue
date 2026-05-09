<template>
  <div class="question-list">
    <div class="list-header">
      <div class="header-left">
        <h2>{{ datasetLabel }}</h2>
        <span class="question-count">共 {{ questions.length }} 题</span>
      </div>
      <div class="header-right">
        <span class="tested-count">{{ testedCount }} 已测试</span>
        <span class="accuracy" v-if="accuracy > 0">准确率: {{ accuracy }}%</span>
      </div>
    </div>
    <div class="list-stats-bar">
      <div class="stat-item">
        <span class="stat-label">已测试</span>
        <span class="stat-value">{{ testedCount }}/{{ questions.length }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">准确率</span>
        <span class="stat-value" :style="{color: accuracy >= 80 ? '#52c41a' : accuracy >= 50 ? '#faad14' : '#ff4d4f'}">{{ accuracy }}%</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">正确SQL已执行</span>
        <span class="stat-value">{{ correctExecutedCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">AI SQL已执行</span>
        <span class="stat-value">{{ aiExecutedCount }}</span>
      </div>
    </div>
    <div class="list-body">
      <div
        v-for="q in questions"
        :key="q.index"
        class="question-card"
        :class="{
          'match-true': q.ai_sql_match === true,
          'match-false': q.ai_sql_match === false,
          'not-tested': q.tested === false
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
          <span v-if="q.tested" class="status-icon" :title="q.ai_sql_match ? 'SQL匹配' : 'SQL不匹配'">
            {{ q.ai_sql_match ? '✅' : '❌' }}
          </span>
          <span v-else class="status-icon pending">⏳</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { getDatasetQuestions } from './api.js'

const emit = defineEmits(['open-detail'])
const props = defineProps({
  datasetName: String
})

const questions = ref([])
const datasetLabel = ref('')

const testedCount = computed(() => questions.value.filter(q => q.tested).length)
const correctExecutedCount = computed(() => questions.value.filter(q => q.correct_executed).length)
const aiExecutedCount = computed(() => questions.value.filter(q => q.ai_executed).length)

const accuracy = computed(() => {
  const tested = questions.value.filter(q => q.tested)
  if (tested.length === 0) return 0
  const matched = tested.filter(q => q.ai_sql_match).length
  return Math.round(matched / tested.length * 100)
})

function openDetail(index) {
  emit('open-detail', props.datasetName, index)
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
  datasetLabel.value = labels[name] || name
  try {
    const res = await getDatasetQuestions(name)
    questions.value = res.data.questions || []
  } catch (e) {
    console.error('Failed to load questions:', e)
    questions.value = []
  }
}, { immediate: true })
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
}

.accuracy {
  color: #667eea;
  font-weight: 600;
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

.status-icon {
  font-size: 20px;
}

.status-icon.pending {
  opacity: 0.4;
}
</style>

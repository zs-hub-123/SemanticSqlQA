<template>
  <div class="test-layout">
    <TestSidebar
      :currentDataset="currentDataset"
      @select-dataset="onSelectDataset"
      @show-stats="onShowStats"
    />
    <div class="test-content">
      <QuestionList
        v-if="view === 'list' && currentDataset"
        :datasetName="currentDataset"
        @open-detail="onOpenDetail"
      />
      <QuestionDetail
        v-else-if="view === 'detail'"
        :datasetName="currentDataset"
        :questionIndex="currentQuestionIndex"
        @back="onBackToList"
      />
      <StatsView
        v-else-if="view === 'stats'"
        @back="onBackFromStats"
      />
      <div v-else class="empty-state">
        <div class="empty-icon">📋</div>
        <h2>SQL智能问答测试套件</h2>
        <p>请从左侧选择一个数据集开始测试</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import TestSidebar from './TestSidebar.vue'
import QuestionList from './QuestionList.vue'
import QuestionDetail from './QuestionDetail.vue'
import StatsView from './StatsView.vue'

const emit = defineEmits([])

const view = ref('welcome')
const currentDataset = ref('')
const currentQuestionIndex = ref(0)

function onSelectDataset(name) {
  currentDataset.value = name
  view.value = 'list'
}

function onOpenDetail(datasetName, index) {
  currentDataset.value = datasetName
  currentQuestionIndex.value = index
  view.value = 'detail'
}

function onBackToList() {
  view.value = 'list'
}

function onShowStats() {
  view.value = 'stats'
}

function onBackFromStats() {
  view.value = currentDataset.value ? 'list' : 'welcome'
}
</script>

<style scoped>
.test-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.test-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f5f7fa;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #999;
}

.empty-icon {
  font-size: 64px;
}

.empty-state h2 {
  font-size: 22px;
  color: #333;
}

.empty-state p {
  font-size: 14px;
  color: #999;
}
</style>

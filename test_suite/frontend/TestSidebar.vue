<template>
  <div class="test-sidebar">
    <div class="sidebar-header">
      <h2>数据集目录</h2>
      <button class="btn-back" @click="goBack">返回主界面</button>
    </div>
    <div class="sidebar-divider"></div>
    <div class="dataset-list">
      <div
        v-for="ds in datasets"
        :key="ds.name"
        class="dataset-item"
        :class="{ active: currentDataset === ds.name }"
        @click="selectDataset(ds.name)"
      >
        <div class="dataset-icon">📊</div>
        <div class="dataset-info">
          <span class="dataset-name">{{ ds.label }}</span>
          <span class="dataset-count">{{ ds.count }} 题</span>
        </div>
        <div class="dataset-badge" v-if="ds.stats">
          <span class="badge" :class="getBadgeClass(ds.stats.accuracy)">
            {{ ds.stats.accuracy }}%
          </span>
        </div>
      </div>
    </div>
    <div class="sidebar-divider"></div>
    <div class="sidebar-footer">
      <button class="btn-stats" @click="showStats">
        总体统计
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getDatasets } from './api.js'

const router = useRouter()
const emit = defineEmits(['select-dataset', 'show-stats'])
const props = defineProps({
  currentDataset: String
})

const datasets = ref([])

function selectDataset(name) {
  emit('select-dataset', name)
}

function showStats() {
  emit('show-stats')
}

function goBack() {
  router.push('/')
}

function getBadgeClass(accuracy) {
  if (accuracy >= 80) return 'badge-success'
  if (accuracy >= 50) return 'badge-warning'
  return 'badge-danger'
}

onMounted(async () => {
  try {
    const res = await getDatasets()
    datasets.value = res.data.datasets || []
  } catch (e) {
    console.error('Failed to load datasets:', e)
  }
})
</script>

<style scoped>
.test-sidebar {
  width: 280px;
  min-width: 280px;
  height: 100vh;
  background: #fff;
  border-right: 1px solid #eee;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 16px;
}

.sidebar-header h2 {
  font-size: 18px;
  color: #333;
  margin-bottom: 12px;
}

.btn-back {
  width: 100%;
  padding: 8px 12px;
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
}

.sidebar-divider {
  height: 1px;
  background: #eee;
  margin: 12px 0;
}

.dataset-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin: 4px 0;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.dataset-item:hover {
  background: #e8ecf8;
}

.dataset-item.active {
  background: #e8ecf8;
  border-color: #667eea;
}

.dataset-icon {
  font-size: 20px;
  margin-right: 12px;
}

.dataset-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.dataset-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.dataset-count {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}

.badge-success {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.badge-warning {
  background: #fffbe6;
  color: #faad14;
  border: 1px solid #ffe58f;
}

.badge-danger {
  background: #fff2f0;
  color: #ff4d4f;
  border: 1px solid #ffccc7;
}

.btn-stats {
  width: 100%;
  padding: 10px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: opacity 0.2s;
}

.btn-stats:hover {
  opacity: 0.9;
}
</style>

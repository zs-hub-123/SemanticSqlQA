<template>
  <div class="stats">
    <div class="stat-item">
      <span class="stat-label">📝 对话数</span>
      <span class="stat-value">{{ conversationCount }}</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">⏱️ 平均耗时</span>
      <span class="stat-value">{{ avgTime }}s</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">💰 总耗时</span>
      <span class="stat-value">{{ totalTime.toFixed(1) }}s</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  conversationCount: { type: Number, default: 0 },
  totalTime: { type: Number, default: 0 }
})

const avgTime = computed(() => {
  if (props.conversationCount === 0) return '0.0'
  return (props.totalTime / props.conversationCount).toFixed(1)
})
</script>

<style scoped>
.stats {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
  color: #667eea;
}
</style>

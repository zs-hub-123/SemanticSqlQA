<template>
  <div class="model-selector">
    <label class="selector-label">当前模型:</label>
    <select v-model="selectedModel" @change="handleSwitch" class="model-select">
      <option :value="false">Qwen3-235B-A22B (主)</option>
      <option :value="true">Qwen3-32B-FP8 (备)</option>
    </select>
    <span v-if="switching" class="switching-hint">切换中...</span>
    <span v-if="error" class="error-hint">{{ error }}</span>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['model-changed'])

const selectedModel = ref(false)
const switching = ref(false)
const error = ref('')

async function loadCurrentModel() {
  try {
    const res = await fetch('/api/model/current')
    const data = await res.json()
    selectedModel.value = data.use_backup
  } catch (e) {
    console.error('Failed to load model info:', e)
  }
}

async function handleSwitch() {
  switching.value = true
  error.value = ''
  try {
    const res = await fetch('/api/model/switch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ use_backup: selectedModel.value })
    })
    const data = await res.json()
    if (data.success) {
      emit('model-changed', {
        use_backup: data.use_backup,
        current_model: data.current_model
      })
    }
  } catch (e) {
    error.value = '切换失败'
    console.error('Failed to switch model:', e)
  } finally {
    switching.value = false
  }
}

onMounted(loadCurrentModel)
</script>

<style scoped>
.model-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selector-label {
  font-size: 12px;
  color: #666;
}

.model-select {
  padding: 4px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
  background: white;
  cursor: pointer;
}

.model-select:hover {
  border-color: #40a9ff;
}

.switching-hint {
  font-size: 11px;
  color: #999;
}

.error-hint {
  font-size: 11px;
  color: #ff4d4f;
}
</style>

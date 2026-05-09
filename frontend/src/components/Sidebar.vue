<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <h2>📋 会话管理</h2>
      <button class="btn-primary" @click="handleNewSession">➕ 新建会话</button>
    </div>

    <div class="sidebar-divider"></div>

    <div class="session-list">
      <h3>📁 历史会话 (共{{ sessions.length }}个)</h3>
      <div v-if="sessions.length === 0" class="empty-sessions">
        <span>暂无历史会话</span>
      </div>
      <div
        v-for="session in sessions"
        :key="session.session_id"
        class="session-item"
        :class="{ active: session.session_id === chatStore.state.currentSessionId }"
      >
        <div class="session-main" @click="handleSwitchSession(session.session_id)">
          <span class="session-icon">{{ session.session_id === chatStore.state.currentSessionId ? '📌' : '📄' }}</span>
          <span class="session-title">{{ truncateText(session.title || '未命名会话', 14) }}</span>
        </div>
        <button
          class="delete-btn"
          @click.stop="handleDeleteSession(session.session_id)"
          title="删除此会话"
        >❌</button>
      </div>
    </div>

    <div class="sidebar-divider"></div>

    <div class="nav-section">
      <button class="btn-test-nav" @click="goToTest">🧪 测试套件</button>
    </div>

    <div class="sidebar-divider"></div>

    <div class="system-status">
      <h3>📊 系统状态</h3>
      <div v-if="health" class="status-healthy">
        <span>✅ 后端服务正常</span>
        <span class="caption">🤖 {{ health.model_name || 'N/A' }}</span>
        <span class="caption">📐 {{ health.schema_loaded ? '已加载' : '未加载' }}</span>
      </div>
      <div v-else class="status-error">
        <span>❌ 后端服务未启动</span>
        <span class="caption">请运行: python app.py</span>
      </div>
    </div>

    <div class="sidebar-divider"></div>

    <div class="sidebar-footer">
      <h3>💡 使用说明</h3>
      <p>1. 点击示例问题或输入问题</p>
      <p>2. AI自动支持多轮对话</p>
      <p>3. 会话自动永久保存</p>
      <p>4. 点击历史会话切换</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat.js'
import { healthCheck } from '../api/index.js'

const router = useRouter()
const chatStore = useChatStore()
const sessions = ref([])
const health = ref(null)

function truncateText(text, maxLength) {
  return text.length <= maxLength ? text : text.substring(0, maxLength) + '...'
}

function handleNewSession() {
  chatStore.newSession()
  refreshSessions()
}

function handleSwitchSession(sessionId) {
  chatStore.switchSession(sessionId)
}

function handleDeleteSession(sessionId) {
  chatStore.deleteSessionFromStorage(sessionId)
  refreshSessions()
}

function refreshSessions() {
  sessions.value = chatStore.loadSessions()
}

function checkHealth() {
  healthCheck()
    .then(res => { health.value = res.data })
    .catch(() => { health.value = null })
}

function goToTest() {
  router.push('/test')
}

onMounted(() => {
  refreshSessions()
  checkHealth()
  setInterval(checkHealth, 30000)
})

defineExpose({ refreshSessions })
</script>

<style scoped>
.sidebar {
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
  font-size: 16px;
  margin-bottom: 12px;
  color: #333;
}

.sidebar-divider {
  height: 1px;
  background: #eee;
  margin: 12px 0;
}

.session-list h3 {
  font-size: 14px;
  margin-bottom: 10px;
  color: #666;
}

.empty-sessions {
  padding: 16px;
  text-align: center;
  color: #999;
  font-size: 13px;
  background: #f8f9fa;
  border-radius: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin: 4px 0;
  background: #f0f2f6;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 13px;
  overflow: hidden;
}

.session-main {
  flex: 1;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.session-item:hover {
  background: #e0e4ea;
}

.session-item.active {
  background: #e8ecf8;
}

.session-icon {
  margin-right: 8px;
  flex-shrink: 0;
}

.session-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12px;
  padding: 4px 6px;
  opacity: 0;
  transition: opacity 0.2s;
  flex-shrink: 0;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  opacity: 1;
  transform: scale(1.1);
}

.system-status h3 {
  font-size: 14px;
  margin-bottom: 10px;
  color: #666;
}

.status-healthy,
.status-error {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
}

.status-healthy span:first-child {
  color: #52c41a;
}

.status-error span:first-child {
  color: #ff4d4f;
}

.caption {
  color: #999 !important;
  font-size: 12px !important;
}

.sidebar-footer h3 {
  font-size: 14px;
  margin-bottom: 8px;
  color: #666;
}

.sidebar-footer p {
  font-size: 12px;
  color: #999;
  margin: 4px 0;
}

.btn-primary {
  width: 100%;
  padding: 8px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: opacity 0.2s;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-test-nav {
  width: 100%;
  padding: 10px 12px;
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: opacity 0.2s;
}

.btn-test-nav:hover {
  opacity: 0.9;
}
</style>

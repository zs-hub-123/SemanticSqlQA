<template>
  <div class="app-container">
    <Sidebar ref="sidebarRef" />

    <div class="main-area">
      <header class="main-header">
        <h1>🤖 AI智能问答系统</h1>
      </header>

      <div class="content-wrapper">
        <ExampleList @select="handleExampleSelect" />

        <div class="divider"></div>

        <div class="chat-section">
          <h3>💬 对话历史</h3>

          <div v-if="chatStore.state.messages.length === 0" class="welcome">
            👋 欢迎使用AI智能问答系统！请输入您的问题。
          </div>

          <div class="message-list">
            <ChatMessage
              v-for="(msg, index) in chatStore.state.messages"
              :key="index"
              :message="msg"
            />
          </div>
        </div>

        <StatsBar
          v-if="chatStore.state.conversationCount > 0"
          :conversation-count="chatStore.state.conversationCount"
          :total-time="chatStore.state.totalTime"
        />

        <div class="divider"></div>
      </div>

      <InputBar ref="inputBarRef" />
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import Sidebar from '../components/Sidebar.vue'
import ExampleList from '../components/ExampleList.vue'
import ChatMessage from '../components/ChatMessage.vue'
import StatsBar from '../components/StatsBar.vue'
import InputBar from '../components/InputBar.vue'
import { useChatStore } from '../stores/chat.js'

const chatStore = useChatStore()
const sidebarRef = ref(null)
const inputBarRef = ref(null)

function handleExampleSelect(question) {
  nextTick(() => {
    if (inputBarRef.value) {
      inputBarRef.value.setText(question)
    }
  })
}
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-header {
  padding: 20px 24px;
  text-align: center;
  border-bottom: 1px solid #eee;
  background: white;
}

.main-header h1 {
  color: #667eea;
  font-size: 24px;
}

.content-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 24px;
}

.divider {
  height: 1px;
  background: #eee;
  margin: 16px 0;
}

.chat-section {
  padding-bottom: 16px;
}

.chat-section h3 {
  margin-bottom: 12px;
  font-size: 16px;
  color: #333;
}

.welcome {
  padding: 24px;
  text-align: center;
  color: #666;
  background: #f8f9fa;
  border-radius: 12px;
  margin-bottom: 16px;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>

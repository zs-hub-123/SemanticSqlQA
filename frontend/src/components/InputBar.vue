<template>
  <div class="input-area">
    <div class="input-wrapper">
      <input
        ref="inputRef"
        v-model="inputText"
        type="text"
        class="question-input"
        placeholder="请输入您的自然语言问题..."
        :disabled="chatStore.state.isLoading"
        @keyup.enter="handleSubmit"
      />
      <button
        class="submit-btn"
        :disabled="chatStore.state.isLoading || !inputText.trim()"
        @click="handleSubmit"
      >
        {{ chatStore.state.isLoading ? '思考中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useChatStore } from '../stores/chat.js'
import { askQuestionStream } from '../api/index.js'

const chatStore = useChatStore()
const inputText = ref('')
const inputRef = ref(null)

function setText(text) {
  inputText.value = text
}

async function handleSubmit() {
  const text = inputText.value.trim()
  if (!text || chatStore.state.isLoading) return

  inputText.value = ''
  chatStore.setLoading(true)

  const userMsg = {
    role: 'user',
    content: text
  }
  chatStore.addMessage(userMsg)

  chatStore.addMessage({
    role: 'assistant',
    type: 'loading',
    content: '🤔 AI正在思考中...'
  })

  const assistantMsgIndex = chatStore.state.messages.length - 1
  const startTime = Date.now()

  let streamedContent = ''
  let finalData = null

  try {
    await askQuestionStream(text, true, {
      onStart: () => {},
      onChunk: (content) => {
        streamedContent += content
        const messages = [...chatStore.state.messages]
        messages[assistantMsgIndex] = {
          role: 'assistant',
          type: 'streaming',
          content: streamedContent
        }
        chatStore.state.messages = messages
      },
      onDone: (data) => {
        finalData = data.result || data
      },
      onError: (error) => {
        const messages = [...chatStore.state.messages]
        messages[assistantMsgIndex] = {
          role: 'assistant',
          type: 'error',
          content: error || '请求失败'
        }
        chatStore.state.messages = messages
      }
    })

    const elapsed = (Date.now() - startTime) / 1000

    if (finalData) {
      const messages = [...chatStore.state.messages]
      messages[assistantMsgIndex] = {
        role: 'assistant',
        type: 'result',
        sql: finalData.sql || '',
        explanation: finalData.explanation || '',
        tables_used: finalData.tables_used || [],
        elapsed_time: finalData.elapsed_time || elapsed,
        query_result: finalData.query_result || null
      }
      chatStore.state.conversationCount++
      chatStore.state.totalTime += finalData.elapsed_time || elapsed
      chatStore.state.messages = messages
    }
  } catch (err) {
    console.error('InputBar错误:', err)
    const messages = [...chatStore.state.messages]
    messages[assistantMsgIndex] = {
      role: 'assistant',
      type: 'error',
      content: err?.message || '无法连接到后端服务，请确保后端已启动'
    }
    chatStore.state.messages = messages
  }

  chatStore.setLoading(false)
  chatStore.saveSessions()
}

function focusInput() {
  inputRef.value && inputRef.value.focus()
}

defineExpose({ setText, focusInput })
</script>

<style scoped>
.input-area {
  padding: 16px 24px;
  background: white;
  border-top: 1px solid #eee;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  max-width: 100%;
}

.question-input {
  flex: 1;
  padding: 12px 18px;
  border: 2px solid #e8e8e8;
  border-radius: 24px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.question-input:focus {
  border-color: #667eea;
}

.question-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.submit-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 24px;
  font-size: 14px;
  cursor: pointer;
  transition: opacity 0.2s;
  white-space: nowrap;
}

.submit-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>

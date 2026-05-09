<template>
  <div class="chat-message" :class="message.role">
    <div class="message-content">
      <div v-if="message.role === 'user'" class="user-bubble">
        {{ message.content }}
      </div>
      <div v-else>
        <div v-if="message.type === 'result'" class="ai-bubble">
          <div class="ai-header">
            <span class="ai-avatar">🤖</span>
            <span class="ai-name">AI助手</span>
          </div>
          <div class="ai-body">
            <div v-if="message.sql" class="sql-block">
              <div class="sql-label">
                <span>📊 生成的SQL:</span>
                <button class="copy-btn" @click="copySql" :class="{ copied: copied }">
                  {{ copied ? '✅ 已复制' : '📋 复制' }}
                </button>
              </div>
              <pre class="sql-code"><code>{{ formatSql(message.sql) }}</code></pre>
            </div>

            <div v-if="message.query_result" class="result-block">
              <div class="result-header">
                <span>📋 查询结果</span>
                <span class="result-count">{{ message.query_result.row_count || 0 }} 条记录</span>
              </div>

              <div v-if="message.query_result.rows && message.query_result.rows.length > 0" class="table-wrapper">
                <table class="result-table">
                  <thead>
                    <tr>
                      <th v-for="col in message.query_result.columns" :key="col">{{ col }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, rowIdx) in message.query_result.rows" :key="rowIdx">
                      <td v-for="(cell, colIdx) in row" :key="colIdx">
                        {{ cell === null ? '<NULL>' : cell }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div v-else-if="message.query_result.row_count === 0" class="result-empty">
                查询成功，但没有返回任何数据
              </div>

              <div v-else-if="message.query_result.error" class="result-error">
                ❌ 查询失败: {{ message.query_result.error }}
              </div>
            </div>

            <div v-if="message.explanation" class="explanation">
              💬 {{ message.explanation }}
            </div>

            <div v-if="message.tables_used && message.tables_used.length > 0 && message.sql" class="tables">
              📋 涉及表: <span v-for="t in message.tables_used" :key="t" class="table-tag">`{{ t }}`</span>
            </div>

            <div v-if="message.elapsed_time" class="elapsed">
              ⏱️ 总耗时: {{ message.elapsed_time.toFixed(2) }}秒
            </div>
          </div>
        </div>

        <div v-else-if="message.type === 'error'" class="error-bubble">
          <div class="error-header">
            <span class="error-icon">❌</span>
            <span>错误</span>
          </div>
          <div class="error-body">
            {{ message.content }}
          </div>
        </div>

        <div v-else-if="message.type === 'loading'" class="loading-bubble">
          <span class="loading-dot">·</span>
          <span class="loading-dot">·</span>
          <span class="loading-dot">·</span>
          <span class="loading-text">AI正在思考</span>
        </div>

        <div v-else-if="message.type === 'streaming'" class="ai-bubble">
          <div class="ai-header">
            <span class="ai-avatar">🤖</span>
            <span class="ai-name">AI助手</span>
            <span class="streaming-indicator">生成中...</span>
          </div>
          <div class="ai-body">
            <div class="streaming-content">{{ message.content }}</div>
          </div>
        </div>

        <div v-else class="ai-bubble">
          <div class="ai-header">
            <span class="ai-avatar">🤖</span>
            <span class="ai-name">AI助手</span>
          </div>
          <div class="ai-body">
            {{ message.content }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const copied = ref(false)

function copySql() {
  if (!props.message.sql) return
  navigator.clipboard.writeText(props.message.sql).then(() => {
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  })
}

function formatSql(sql) {
  if (!sql) return ''

  const keywords = ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'ORDER BY', 'GROUP BY', 'HAVING', 'LIMIT', 'OFFSET', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN', 'ON', 'AS', 'DISTINCT', 'COUNT\\(', 'SUM\\(', 'AVG\\(', 'MAX\\(', 'MIN\\(', 'IN\\(', 'LIKE', 'BETWEEN', 'ASC', 'DESC', 'SET', 'VALUES', 'INSERT INTO', 'UPDATE', 'DELETE FROM']

  let formatted = sql.trim()

  keywords.forEach(kw => {
    const regex = new RegExp(`\\b${kw}\\b`, 'gi')
    formatted = formatted.replace(regex, `\n${kw}`)
  })

  const lines = formatted.split('\n').filter(line => line.trim())
  const indented = lines.map((line, i) => {
    if (i === 0) return line.trim()
    const upper = line.trim()
    if (upper.startsWith('SELECT') || upper.startsWith('FROM') || upper.startsWith('WHERE') || upper.startsWith('ORDER BY') || upper.startsWith('GROUP BY') || upper.startsWith('HAVING') || upper.startsWith('LIMIT')) {
      return '  ' + line.trim()
    }
    return '    ' + line.trim()
  })

  return indented.join('\n')
}
</script>

<style scoped>
.chat-message {
  display: flex;
  margin: 12px 0;
}

.chat-message.user {
  justify-content: flex-end;
}

.chat-message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 90%;
}

/* 用户气泡 */
.user-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 18px;
  border-radius: 20px 20px 4px 20px;
  line-height: 1.6;
  word-break: break-word;
  font-size: 14px;
  max-width: 100%;
}

/* AI 气泡 */
.ai-bubble {
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 20px 20px 20px 4px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.ai-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.ai-avatar {
  font-size: 18px;
}

.ai-name {
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.ai-body {
  padding: 14px 16px;
}

/* SQL 块 */
.sql-block {
  margin-bottom: 12px;
}

.sql-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 13px;
  color: #333;
}

.copy-btn {
  background: #f0f2f6;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 2px 10px;
  font-size: 12px;
  cursor: pointer;
  color: #667eea;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.copy-btn.copied {
  background: #52c41a;
  color: white;
  border-color: #52c41a;
}

.sql-code {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 14px;
  border-radius: 10px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.7;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.sql-code code {
  font-family: 'Consolas', 'Monaco', monospace;
}

/* 查询结果块 */
.result-block {
  margin-bottom: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  overflow: hidden;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: #f8f9fa;
  border-bottom: 1px solid #e8e8e8;
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.result-count {
  font-weight: normal;
  color: #667eea;
  font-size: 12px;
}

.table-wrapper {
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

.result-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.result-table thead {
  position: sticky;
  top: 0;
  z-index: 1;
}

.result-table th {
  background: #667eea;
  color: white;
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
  white-space: nowrap;
  border: none;
}

.result-table td {
  padding: 9px 14px;
  border-bottom: 1px solid #f0f0f0;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #333;
}

.result-table tbody tr:nth-child(even) {
  background: #fafafa;
}

.result-table tbody tr:hover {
  background: #f0f4ff;
}

.result-empty {
  padding: 20px;
  text-align: center;
  color: #999;
  font-size: 13px;
}

.result-error {
  padding: 12px 14px;
  color: #ff4d4f;
  font-size: 13px;
}

/* 说明、表格、耗时 */
.explanation {
  margin-bottom: 8px;
  line-height: 1.6;
  color: #444;
  font-size: 14px;
}

.tables {
  margin-bottom: 6px;
  font-size: 13px;
  color: #666;
}

.table-tag {
  background: #e8ecf8;
  padding: 2px 6px;
  border-radius: 4px;
  margin: 0 2px;
  font-family: monospace;
  color: #667eea;
}

.elapsed {
  font-size: 12px;
  color: #999;
}

/* 错误气泡 */
.error-bubble {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 20px 20px 20px 4px;
  overflow: hidden;
}

.error-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-bottom: 1px solid #ffd8d3;
  background: #fff1ed;
  font-weight: 600;
  font-size: 13px;
  color: #ff4d4f;
}

.error-icon {
  font-size: 16px;
}

.error-body {
  padding: 12px 16px;
  color: #ff4d4f;
  font-size: 14px;
}

/* 加载气泡 */
.loading-bubble {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 14px 18px;
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 20px 20px 20px 4px;
}

.loading-dot {
  font-size: 20px;
  color: #667eea;
  animation: bounce 1.2s infinite;
}

.loading-dot:nth-child(2) { animation-delay: 0.2s; }
.loading-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

.loading-text {
  margin-left: 6px;
  font-size: 13px;
  color: #999;
}

.streaming-indicator {
  font-size: 12px;
  color: #667eea;
  margin-left: auto;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.streaming-content {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}
</style>

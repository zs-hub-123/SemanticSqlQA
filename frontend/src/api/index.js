import axios from 'axios'

// 使用相对路径，通过Vite代理访问后端
const API_BASE = ''

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 180000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const askQuestion = (question, useHistory = true) => {
  return apiClient.post('/api/ask', { question, use_history: useHistory })
}

export const askQuestionStream = (question, useHistory = true, callbacks = {}) => {
  const { onStart, onChunk, onDone, onError } = callbacks

  return new Promise(async (resolve, reject) => {
    try {
      console.log('[API] 开始请求 /api/ask/stream')
      onStart && onStart()

      const response = await fetch(`/api/ask/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, use_history: useHistory })
      })

      console.log('[API] 响应状态:', response.status)

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'chunk') {
                onChunk && onChunk(data.content, data.elapsed)
              } else if (data.type === 'done') {
                onDone && onDone(data)
                resolve(data)
              } else if (data.type === 'error') {
                onError && onError(data.error)
                reject(new Error(data.error))
              }
            } catch (e) {
              console.warn('Failed to parse SSE data:', e)
            }
          }
        }
      }
    } catch (e) {
      console.error('[API] 请求失败:', e.message)
      onError && onError(e.message)
      reject(e)
    }
  })
}

export const resetHistory = () => {
  return apiClient.post('/api/reset')
}

export const healthCheck = () => {
  return apiClient.get('/api/health')
}

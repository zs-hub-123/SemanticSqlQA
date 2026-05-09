import { reactive } from 'vue'

const STORAGE_KEY = 'sql_qa_sessions'
const CURRENT_KEY = 'sql_qa_current'

const defaultState = () => ({
  currentSessionId: generateSessionId(),
  messages: [],
  conversationCount: 0,
  totalTime: 0.0,
  isLoading: false,
  pendingQuestion: null
})

let state = reactive(defaultState())

function generateSessionId() {
  const now = new Date()
  return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}_${String(now.getMilliseconds()).padStart(6, '0')}`
}

function generateTitle(messages) {
  if (!messages || messages.length === 0) return '新会话'
  const firstUser = messages.find(m => m.role === 'user')
  if (firstUser) {
    return firstUser.content.length > 25 ? firstUser.content.substring(0, 25) + '...' : firstUser.content
  }
  return '新会话'
}

function saveSessions() {
  try {
    const sessions = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    const idx = sessions.findIndex(s => s.session_id === state.currentSessionId)
    const sessionData = {
      session_id: state.currentSessionId,
      title: generateTitle(state.messages),
      messages: state.messages,
      created_at: idx >= 0 ? sessions[idx].created_at : new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    if (idx >= 0) {
      sessions[idx] = sessionData
    } else {
      sessions.unshift(sessionData)
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
    localStorage.setItem(CURRENT_KEY, state.currentSessionId)
  } catch (e) {
    console.error('Failed to save sessions:', e)
  }
}

function loadSessions() {
  try {
    const sessions = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    return sessions.sort((a, b) => (b.updated_at || '').localeCompare(a.updated_at || ''))
  } catch (e) {
    return []
  }
}

function loadCurrentSession() {
  try {
    const sessions = loadSessions()
    const currentId = localStorage.getItem(CURRENT_KEY)
    const session = sessions.find(s => s.session_id === currentId)
    if (session) {
      state.currentSessionId = session.session_id
      state.messages = session.messages || []
      state.conversationCount = (session.messages || []).filter(m => m.role === 'user').length
      state.totalTime = (session.messages || []).filter(m => m.type === 'result').reduce((sum, m) => sum + (m.elapsed_time || 0), 0)
    }
  } catch (e) {
    console.error('Failed to load session:', e)
  }
}

function clearCurrentSession() {
  state.messages = []
  state.conversationCount = 0
  state.totalTime = 0.0
}

function addMessage(msg) {
  state.messages.push(msg)
  saveSessions()
}

function setLoading(loading) {
  state.isLoading = loading
}

function setPendingQuestion(q) {
  state.pendingQuestion = q
}

function newSession() {
  state.currentSessionId = generateSessionId()
  clearCurrentSession()
  saveSessions()
}

function switchSession(sessionId) {
  state.currentSessionId = sessionId
  const sessions = loadSessions()
  const session = sessions.find(s => s.session_id === sessionId)
  if (session) {
    state.messages = session.messages || []
    state.conversationCount = (session.messages || []).filter(m => m.role === 'user').length
    state.totalTime = (session.messages || []).filter(m => m.type === 'result').reduce((sum, m) => sum + (m.elapsed_time || 0), 0)
  }
  localStorage.setItem(CURRENT_KEY, sessionId)
}

function deleteSessionFromStorage(sessionId) {
  try {
    const sessions = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    const filtered = sessions.filter(s => s.session_id !== sessionId)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
    if (localStorage.getItem(CURRENT_KEY) === sessionId) {
      localStorage.removeItem(CURRENT_KEY)
      if (filtered.length > 0) {
        state.currentSessionId = filtered[0].session_id
        state.messages = filtered[0].messages || []
        state.conversationCount = (filtered[0].messages || []).filter(m => m.role === 'user').length
        state.totalTime = (filtered[0].messages || []).filter(m => m.type === 'result').reduce((sum, m) => sum + (m.elapsed_time || 0), 0)
        localStorage.setItem(CURRENT_KEY, state.currentSessionId)
      } else {
        state.currentSessionId = generateSessionId()
        clearCurrentSession()
        saveSessions()
      }
    }
  } catch (e) {
    console.error('Failed to delete session:', e)
  }
}

loadCurrentSession()

export function useChatStore() {
  return {
    state,
    addMessage,
    setLoading,
    setPendingQuestion,
    newSession,
    switchSession,
    clearCurrentSession,
    deleteSessionFromStorage,
    loadSessions,
    saveSessions
  }
}

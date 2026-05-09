import axios from 'axios'

const apiClient = axios.create({
  baseURL: '',
  timeout: 300000,
  headers: { 'Content-Type': 'application/json' }
})

export function getDatasets() {
  return apiClient.get('/api/test/datasets')
}

export function getDatasetQuestions(datasetName, page = 1, pageSize = 10) {
  return apiClient.get(`/api/test/dataset/${datasetName}`, { params: { page, page_size: pageSize } })
}

export function getQuestionDetail(datasetName, questionIndex) {
  return apiClient.get(`/api/test/question/${datasetName}/${questionIndex}`)
}

export function generateAiSql(datasetName, questionIndex) {
  return apiClient.post(`/api/test/generate-ai/${datasetName}/${questionIndex}`)
}

export function executeSql(datasetName, questionIndex, sql, type) {
  return apiClient.post(`/api/test/execute/${datasetName}/${questionIndex}`, { sql, type })
}

export function setMatchStatus(datasetName, questionIndex, matchType, value) {
  return apiClient.post(`/api/test/match/${datasetName}/${questionIndex}`, {
    match_type: matchType,
    value: value
  })
}

export function getDatasetStats(datasetName) {
  return apiClient.get(`/api/test/stats/${datasetName}`)
}

export function getAllStats() {
  return apiClient.get('/api/test/stats')
}

export function resetTestResults(datasetName = null) {
  const params = datasetName ? { dataset_name: datasetName } : {}
  return apiClient.post('/api/test/reset', null, { params })
}

export function startAutoTest(datasetName, interval = 30, skipExisting = true) {
  return apiClient.post(`/api/test/auto-test/start/${datasetName}`, {
    interval,
    skip_existing: skipExisting
  })
}

export function stopAutoTest(taskId) {
  return apiClient.post(`/api/test/auto-test/stop/${taskId}`)
}

export function getAutoTestStatus(taskId) {
  return apiClient.get(`/api/test/auto-test/status/${taskId}`)
}

export function autoMatch(datasetName) {
  return apiClient.post(`/api/test/auto-match/${datasetName}`)
}

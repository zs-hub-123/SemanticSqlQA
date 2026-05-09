import axios from 'axios'

const apiClient = axios.create({
  baseURL: '',
  timeout: 300000,
  headers: { 'Content-Type': 'application/json' }
})

export function getDatasets() {
  return apiClient.get('/api/test/datasets')
}

export function getDatasetQuestions(datasetName) {
  return apiClient.get(`/api/test/dataset/${datasetName}`)
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

export function getDatasetStats(datasetName) {
  return apiClient.get(`/api/test/stats/${datasetName}`)
}

export function getAllStats() {
  return apiClient.get('/api/test/stats')
}

// ============================================================
//  项目管理 API
// ============================================================
import request from './request'

export function getProjects(params) {
  return request.get('/projects', { params })
}

export function getProject(id) {
  return request.get(`/projects/${id}`)
}

export function registerProject(data) {
  return request.post('/projects/register', data)
}

export function updateProject(id, data) {
  return request.put(`/projects/${id}`, data)
}

export function uploadWordContract(projectId, file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post(`/projects/${projectId}/upload-word`, formData, {
    timeout: 180000, // LLM 提取可能耗时较长
  })
}

export function uploadPdfContract(projectId, file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post(`/projects/${projectId}/upload-pdf`, formData, {
    timeout: 180000, // OCR + LLM 提取可能耗时较长
  })
}

export function verifyContract(projectId) {
  return request.post(`/projects/${projectId}/verify`)
}

export function analyzeVersions(projectId) {
  return request.post(`/projects/${projectId}/analyze-versions`, null, {
    timeout: 180000, // LLM 分析可能耗时较长
  })
}

export function getContracts(projectId) {
  return request.get(`/projects/${projectId}/contracts`)
}

export function submitProject(projectId) {
  return request.post(`/projects/${projectId}/submit`)
}

export function auditProject(projectId, data) {
  return request.post(`/projects/${projectId}/audit`, data)
}

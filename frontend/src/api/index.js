/**
 * 后端 API 调用封装
 * 所有接口调用统一走这里，组件不直接写 fetch
 */

const BASE_URL = 'http://localhost:8000'

async function request(url, options = {}) {
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  }
  const res = await fetch(`${BASE_URL}${url}`, config)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.detail || err.error || `HTTP ${res.status}`)
  }
  return res.json()
}

// ── GET 请求 ──

export function fetchHealth() {
  return request('/api/health')
}

export function fetchDepartments() {
  return request('/api/departments')
}

export function fetchIndicators(params = {}) {
  const qs = new URLSearchParams()
  if (params.department_id) qs.set('department_id', params.department_id)
  if (params.year) qs.set('year', params.year)
  if (params.month) qs.set('month', params.month)
  if (params.metrics) qs.set('metrics', params.metrics)
  const query = qs.toString()
  return request(`/api/indicators${query ? '?' + query : ''}`)
}

export function fetchAnomalies(params = {}) {
  const qs = new URLSearchParams()
  if (params.department_id) qs.set('department_id', params.department_id)
  if (params.severity) qs.set('severity', params.severity)
  if (params.year) qs.set('year', params.year)
  const query = qs.toString()
  return request(`/api/anomalies${query ? '?' + query : ''}`)
}

// ── POST 请求 ──

export function detectAnomalies(body) {
  return request('/api/anomalies/detect', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function queryNL2SQL(body) {
  return request('/api/query/nl2sql', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function generateReport(body) {
  return request('/api/report/generate', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

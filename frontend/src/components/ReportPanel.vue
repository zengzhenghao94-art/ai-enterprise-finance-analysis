<template>
  <div class="bg-white rounded-2xl shadow-sm border border-steep-dove overflow-hidden">
    <!-- 标题栏 -->
    <div class="px-4 py-3 bg-steep-wash border-b border-steep-dove flex items-center justify-between">
      <h3 class="text-sm font-semibold text-steep-ink flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        经营简报
      </h3>
      <div class="flex items-center gap-2">
        <!-- 年份（与右上角同步） -->
        <span class="text-xs text-steep-graphite font-medium bg-steep-fog px-2 py-1 rounded-full">{{ year }}年</span>
        <!-- 月份选择 -->
        <select
          v-model.number="selectedMonth"
          :disabled="generating"
          class="px-2 py-1.5 border border-steep-dove rounded-full text-xs
                 focus:ring-2 focus:ring-steep-blue focus:border-steep-blue outline-none
                 bg-white cursor-pointer disabled:opacity-50 transition-shadow"
        >
          <option v-for="m in 12" :key="m" :value="m">{{ m }}月</option>
        </select>
        <button
          @click="generateReportFn"
          :disabled="generating"
          class="px-3 py-1.5 bg-steep-blue text-white rounded-full text-xs font-medium
                 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed
                 transition-opacity flex items-center gap-1 shrink-0"
        >
          <svg v-if="generating" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {{ generating ? '生成中' : '生成简报' }}
        </button>
        <button
          @click="exportReportFn"
          :disabled="!report || exporting"
          class="px-3 py-1.5 bg-white text-steep-ash border border-steep-dove rounded-full text-xs font-medium
                 hover:bg-steep-fog disabled:opacity-50 disabled:cursor-not-allowed
                 transition-colors flex items-center gap-1 shrink-0"
          title="导出为 ZIP（HTML + 图表）"
        >
          <svg v-if="exporting" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <svg v-else class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          {{ exporting ? '导出中' : '导出' }}
        </button>
      </div>
    </div>

    <!-- 简报内容 -->
    <div class="p-4 max-h-96 overflow-y-auto">
      <!-- 空状态 -->
      <div
        v-if="!report && !error && !generating"
        class="py-8 text-center text-steep-graphite text-sm"
      >
        <div class="text-2xl mb-2">📋</div>
        选择月份，点击"生成简报"自动分析经营数据
      </div>

      <!-- 加载中 -->
      <div v-if="generating" class="py-8 text-center">
        <div class="animate-spin w-6 h-6 border-2 border-steep-blue border-t-transparent rounded-full mx-auto mb-2"></div>
        <div class="text-sm text-steep-graphite">AI 正在生成简报...</div>
      </div>

      <!-- 错误 -->
      <div v-if="error && !generating" class="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-700">
        <div class="font-medium mb-1">⚠️ 生成失败</div>
        {{ error }}
      </div>

      <!-- 生成的简报 -->
      <div v-if="report && !generating" class="space-y-4">
        <!-- 标题 -->
        <div class="text-sm font-semibold text-steep-ink">{{ report.title }}</div>

        <!-- 关键发现 -->
        <div v-if="report.key_findings && report.key_findings.length" class="space-y-1.5">
          <div class="text-xs text-steep-graphite font-medium">🔑 关键发现</div>
          <ul class="space-y-1">
            <li
              v-for="(f, i) in report.key_findings"
              :key="i"
              class="flex items-start gap-2 text-xs text-steep-ash"
            >
              <span class="text-steep-blue mt-0.5">•</span>
              {{ f }}
            </li>
          </ul>
        </div>

        <!-- 简报正文（Markdown 渲染） -->
        <div
          class="text-xs text-steep-ash leading-relaxed border-t border-steep-dove pt-3 prose prose-sm max-w-none"
          v-html="renderedContent"
        ></div>

        <!-- 生成时间 -->
        <div class="text-xs text-steep-graphite">
          生成时间: {{ report.generated_at }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { marked } from 'marked'
import { generateReport } from '../api/index.js'

const props = defineProps({
  departmentId: { type: Number, default: null },
  year: { type: Number, default: 2025 },
})

const report = ref(null)
const generating = ref(false)
const exporting = ref(false)
const error = ref('')
const selectedMonth = ref(new Date().getMonth() + 1)  // 默认当前月

const renderedContent = computed(() => {
  if (!report.value?.content) return ''
  return marked.parse(report.value.content)
})

async function generateReportFn() {
  if (generating.value) return
  generating.value = true
  error.value = ''
  report.value = null

  try {
    const body = {
      department_id: props.departmentId ?? null,
      year: props.year,
      month: selectedMonth.value,
      include_anomalies: true,
    }
    report.value = await generateReport(body)
  } catch (e) {
    error.value = e.message || '简报生成失败，请检查后端服务'
  } finally {
    generating.value = false
  }
}

async function exportReportFn() {
  if (exporting.value || !report.value) return
  exporting.value = true

  try {
    const body = {
      department_id: props.departmentId ?? null,
      year: props.year,
      month: selectedMonth.value,
      include_anomalies: true,
    }
    const resp = await fetch('/api/report/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!resp.ok) {
      // 区分错误类型：HTTP 状态码 → 具体提示
      const statusMap = {
        404: '未找到该月数据，请确认年份和月份',
        400: '请求参数有误，请重试',
        422: '提交数据不合法，请检查输入',
        503: 'AI 服务暂时不可用，请稍后重试',
        500: '服务器内部错误，请联系管理员',
      }
      const err = await resp.json().catch(() => ({}))
      const detail = err.detail || statusMap[resp.status] || '导出失败'
      throw new Error(`[${resp.status}] ${detail}`)
    }
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${props.year}年${selectedMonth.value}月经营分析简报.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = e.message || '导出失败，请检查后端服务'
  } finally {
    exporting.value = false
  }
}
</script>

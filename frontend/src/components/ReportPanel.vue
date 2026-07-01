<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
    <!-- 标题栏 -->
    <div class="px-4 py-3 bg-green-50 border-b border-green-100 flex items-center justify-between">
      <h3 class="text-sm font-semibold text-green-800 flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        经营简报
      </h3>
      <button
        @click="generateReportFn"
        :disabled="generating"
        class="px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs font-medium
               hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed
               transition-colors flex items-center gap-1"
      >
        <svg v-if="generating" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        {{ generating ? '生成中' : '生成简报' }}
      </button>
    </div>

    <!-- 简报内容 -->
    <div class="p-4 max-h-96 overflow-y-auto">
      <!-- 空状态 -->
      <div
        v-if="!report && !error && !generating"
        class="py-8 text-center text-gray-400 text-sm"
      >
        点击"生成简报"自动分析当前经营数据
      </div>

      <!-- 错误 -->
      <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
        {{ error }}
      </div>

      <!-- 生成的简报 -->
      <div v-if="report" class="space-y-4">
        <!-- 标题 -->
        <div class="text-sm font-semibold text-gray-800">{{ report.title }}</div>

        <!-- 关键发现 -->
        <div v-if="report.key_findings && report.key_findings.length" class="space-y-1.5">
          <div class="text-xs text-gray-500 font-medium">🔑 关键发现</div>
          <ul class="space-y-1">
            <li
              v-for="(f, i) in report.key_findings"
              :key="i"
              class="flex items-start gap-2 text-xs text-gray-700"
            >
              <span class="text-blue-500 mt-0.5">•</span>
              {{ f }}
            </li>
          </ul>
        </div>

        <!-- 简报正文（纯文本渲染，不解析 Markdown） -->
        <div class="text-xs text-gray-600 leading-relaxed whitespace-pre-wrap border-t border-gray-100 pt-3">
          {{ report.content }}
        </div>

        <!-- 生成时间 -->
        <div class="text-xs text-gray-400">
          生成时间: {{ report.generated_at }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { generateReport } from '../api/index.js'

const props = defineProps({
  departmentId: { type: [Number, Object], default: null },
  year: { type: Number, default: 2025 },
})

const report = ref(null)
const generating = ref(false)
const error = ref('')

async function generateReportFn() {
  generating.value = true
  error.value = ''
  report.value = null

  try {
    const body = {
      department_id: props.departmentId || null,
      year: props.year,
      month: 6,
      include_anomalies: true,
    }
    report.value = await generateReport(body)
  } catch (e) {
    error.value = e.message || '简报生成失败，请检查后端服务'
  } finally {
    generating.value = false
  }
}
</script>

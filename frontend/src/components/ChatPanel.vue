<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
    <!-- 标题栏 -->
    <div class="px-4 py-3 bg-blue-50 border-b border-blue-100">
      <h3 class="text-sm font-semibold text-blue-800 flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
        智能问数 · 分析助手
      </h3>
    </div>

    <!-- 结果展示区 -->
    <div class="p-4 max-h-96 overflow-y-auto space-y-3">

      <!-- 空状态 / 引导 -->
      <div
        v-if="!result && !loading && !error"
        class="py-4 text-center"
      >
        <div class="text-3xl mb-2">💬</div>
        <div class="text-sm text-gray-600 mb-1">用自然语言提问，AI 自动查数据、做分析</div>
        <div class="text-xs text-gray-400 mb-4">支持查数、对比、排名、趋势分析等多种问法</div>

        <!-- 查数示例 -->
        <div class="text-xs text-gray-400 mb-1.5">📊 数据查询</div>
        <div class="text-xs text-gray-500 space-y-1 mb-3">
          <div
            v-for="(q, i) in sampleLookupQuestions"
            :key="'lookup-' + i"
            class="hover:text-blue-500 cursor-pointer transition-colors"
            @click="quickAsk(q)"
          >
            💡 "{{ q }}"
          </div>
        </div>

        <!-- 分析示例 -->
        <div class="text-xs text-gray-400 mb-1.5">🔍 智能分析</div>
        <div class="text-xs text-gray-500 space-y-1">
          <div
            v-for="(q, i) in sampleAnalysisQuestions"
            :key="'analysis-' + i"
            class="hover:text-blue-500 cursor-pointer transition-colors"
            @click="quickAsk(q)"
          >
            💡 "{{ q }}"
          </div>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="py-8 text-center">
        <div class="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
        <div class="text-sm text-gray-400">AI 正在分析数据...</div>
      </div>

      <!-- 结果面板 -->
      <template v-if="result && !loading">
        <!-- 生成的 SQL -->
        <div class="bg-gray-900 text-green-400 text-xs font-mono rounded-lg p-3 overflow-x-auto">
          <div class="text-gray-500 mb-1">📝 生成 SQL</div>
          {{ result.sql_generated }}
        </div>

        <!-- 有数据的表格 -->
        <div class="overflow-x-auto" v-if="result.result && result.result.length">
          <div class="text-xs text-gray-500 mb-1">📊 查询结果（{{ result.result.length }} 条）</div>
          <table class="w-full text-xs border-collapse">
            <thead>
              <tr class="bg-gray-100">
                <th
                  v-for="key in Object.keys(result.result[0])"
                  :key="key"
                  class="px-2 py-1.5 text-left font-medium text-gray-600 border border-gray-200"
                >
                  {{ key }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in result.result" :key="i" class="hover:bg-gray-50">
                <td
                  v-for="key in Object.keys(result.result[0])"
                  :key="key"
                  class="px-2 py-1 border border-gray-200 text-gray-700"
                >
                  {{ formatCell(row[key]) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 空结果明确提示 -->
        <div
          v-if="result.result && !result.result.length"
          class="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm text-yellow-800"
        >
          <div class="font-medium mb-1">📭 未找到匹配数据</div>
          <div class="text-xs text-yellow-700">
            数据库中暂无可匹配您查询条件的记录。请检查：
            <ul class="list-disc list-inside mt-1 space-y-0.5">
              <li>部门名称是否正确（销售部/生产部/市场部）</li>
              <li>时间范围是否在 2024-2025 年</li>
              <li>查询的指标是否在数据库中存在</li>
            </ul>
          </div>
        </div>

        <!-- 自然语言解释 -->
        <div class="bg-blue-50 rounded-lg p-3 text-sm text-blue-900" v-if="result.explanation">
          <div class="text-xs text-blue-500 mb-1">💡 解读</div>
          {{ result.explanation }}
        </div>

        <!-- 追问建议 -->
        <div v-if="result.result && result.result.length" class="border-t border-gray-100 pt-2">
          <div class="text-xs text-gray-400 mb-1.5">👇 继续追问</div>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="(q, i) in suggestedFollowUps"
              :key="i"
              @click="quickAsk(q)"
              class="px-2 py-1 bg-gray-50 hover:bg-blue-50 hover:text-blue-600 text-xs text-gray-500 rounded-md
                     border border-gray-100 hover:border-blue-200 transition-colors text-left"
            >
              {{ q }}
            </button>
          </div>
        </div>

        <!-- Token 消耗 -->
        <div class="text-xs text-gray-400 text-right" v-if="result.tokens_used">
          Token: {{ result.tokens_used }}
        </div>
      </template>

      <!-- 错误提示 -->
      <div v-if="error && !loading" class="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
        <div class="font-medium mb-1">⚠️ 查询失败</div>
        {{ error }}
      </div>
    </div>

    <!-- 输入区 -->
    <div class="px-4 py-3 border-t border-gray-100 flex gap-2">
      <input
        v-model="query"
        type="text"
        placeholder="输入问题，如：哪个部门利润最高？对比各部门毛利率趋势"
        class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm
               focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        :disabled="loading"
        @keyup.enter="sendQuery"
      />
      <button
        @click="sendQuery"
        :disabled="loading || !query.trim()"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium
               hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
               transition-colors flex items-center gap-1 shrink-0"
      >
        <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span>{{ loading ? '分析中' : '发送' }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { queryNL2SQL } from '../api/index.js'

const props = defineProps({
  departmentId: { type: Number, default: null },
  year: { type: Number, default: 2025 },
})

const query = ref('')
const loading = ref(false)
const result = ref(null)
const error = ref('')

// 当前部门名称（用于动态示例和追问）
const deptName = computed(() => {
  if (!props.departmentId) return '全公司'
  return { 1: '销售部', 2: '生产部', 3: '市场部' }[props.departmentId] || '该部门'
})

// 动态示例问题 — 随部门/年份联动
const sampleLookupQuestions = computed(() => {
  const y = props.year
  if (!props.departmentId) {
    // 全公司
    return [
      `全公司${y}年总收入是多少？`,
      `各部门${y}年上半年净利润对比`,
    ]
  }
  return [
    `${deptName.value}${y}年总收入是多少？`,
    `${deptName.value}上半年的净利润`,
  ]
})

const sampleAnalysisQuestions = computed(() => {
  const y = props.year
  if (!props.departmentId) {
    return [
      `各部门${y}年6月的毛利率排名`,
      `对比各部门${y}年的净利率走势`,
      `哪个部门成本收入比最高？有什么风险？`,
    ]
  }
  return [
    `${deptName.value}${y}年各月毛利率变化趋势`,
    `${deptName.value}的净利率在${y}年是否稳定？`,
    `${deptName.value}${y}年有哪些异常指标需要关注？`,
  ]
})

// 根据查询结果动态生成追问建议
const suggestedFollowUps = computed(() => {
  const y = props.year
  return [
    `${deptName.value}${y}年各月净利润变化趋势是怎样的？`,
    `${deptName.value}${y}年哪个季度表现最好？`,
    `对比${deptName.value}近两年的毛利率变化`,
    `${deptName.value}有哪些异常指标需要关注？`,
  ]
})

function quickAsk(text) {
  query.value = text
  sendQuery()
}

async function sendQuery() {
  if (!query.value.trim() || loading.value) return

  loading.value = true
  error.value = ''
  result.value = null

  try {
    const body = {
      query: query.value.trim(),
      department_id: props.departmentId ?? null,
    }
    result.value = await queryNL2SQL(body)
  } catch (e) {
    error.value = e.message || '查询失败，请检查后端服务是否正常运行'
  } finally {
    loading.value = false
  }
}

function formatCell(v) {
  if (v == null) return '—'
  if (typeof v === 'number') {
    return Number(v).toLocaleString('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  }
  return v
}
</script>

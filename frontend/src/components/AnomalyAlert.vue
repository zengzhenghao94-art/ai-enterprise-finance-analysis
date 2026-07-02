<template>
  <div class="bg-white rounded-2xl border border-steep-dove p-4">
    <div class="flex items-center justify-between mb-3">
      <h4 class="text-sm font-semibold text-steep-ash flex items-center gap-2">
        ⚠️ 异常预警
      </h4>
      <!-- 触发检测按钮 -->
      <button
        @click="runDetection"
        :disabled="detecting"
        class="px-3 py-1.5 bg-steep-wash text-steep-blue rounded-full text-xs font-medium
               hover:bg-steep-sky-wash disabled:opacity-50 disabled:cursor-not-allowed
               transition-colors flex items-center gap-1"
      >
        <svg v-if="detecting" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        {{ detecting ? '检测中' : '重新检测' }}
      </button>
    </div>

    <!-- 汇总 -->
    <div
      v-if="summaryText"
      class="flex items-center gap-2 mb-3 text-xs text-steep-graphite"
    >
      <span>共 {{ anomalies.length }} 条异常：</span>
      <span v-if="backendSummary.high" class="text-steep-crimson font-medium">🔴 {{ backendSummary.high }} 高</span>
      <span v-if="backendSummary.medium" class="text-orange-600 font-medium">🟠 {{ backendSummary.medium }} 中</span>
      <span v-if="backendSummary.low" class="text-yellow-600 font-medium">🟡 {{ backendSummary.low }} 低</span>
    </div>

    <!-- 加载错误 -->
    <div
      v-if="error"
      class="bg-yellow-50 border border-yellow-300 rounded-xl px-3 py-2 text-sm text-yellow-800 flex items-center gap-2"
    >
      <span>⚠️</span>
      {{ error }}
    </div>

    <!-- 加载中 -->
    <div v-if="loading || detecting" class="space-y-2">
      <div v-for="i in 3" :key="i" class="h-14 bg-steep-fog rounded-xl animate-pulse"></div>
    </div>

    <!-- 空状态 -->
    <div
      v-else-if="!anomalies.length"
      class="py-8 text-center text-steep-graphite text-sm"
    >
      <div class="text-2xl mb-2">✅</div>
      <div>未检测到异常</div>
      <div class="text-xs text-steep-slate mt-1">点击"重新检测"运行 ML 异常检测</div>
    </div>

    <!-- 异常列表 -->
    <div v-else class="space-y-3">
      <div
        v-for="a in anomalies"
        :key="a.id"
        :class="severityCardClass(a.severity)"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span
                :class="severityBadgeClass(a.severity)"
                class="px-1.5 py-0.5 rounded text-xs font-medium"
              >
                {{ severityLabel(a.severity) }}
              </span>
              <span class="text-sm font-medium text-steep-ink">
                {{ a.metric_label }}
              </span>
              <span class="text-xs text-steep-graphite">
                {{ a.department_name }} · {{ a.year }}/{{ a.month }}
              </span>
              <!-- 偏离幅度 -->
              <span
                :class="a.deviation_pct < 0 ? 'text-steep-crimson' : 'text-amber-600'"
                class="text-xs font-mono font-medium ml-auto"
                :title="'实际值偏离预期均值 ' + (a.deviation_pct > 0 ? '高' : '低') + Math.abs(a.deviation_pct).toFixed(1) + '%'"
              >
                偏离 {{ a.deviation_pct > 0 ? '+' : '' }}{{ a.deviation_pct.toFixed(1) }}%
              </span>
            </div>

            <!-- 实际值 vs 预期 -->
            <div class="flex items-center gap-3 text-xs mt-1">
              <span class="text-steep-ash">
                实际值: <strong class="text-steep-ink">{{ formatValue(a.actual_value, a.metric_name) }}</strong>
              </span>
              <span class="text-steep-graphite">
                预期范围: {{ a.expected_range }}
              </span>
            </div>

            <!-- LLM 解释 / 数据来源说明 -->
            <div v-if="a.description" class="text-xs text-steep-ash mt-1.5 leading-relaxed">
              💬 {{ a.description }}
            </div>
            <div v-else class="text-xs text-steep-graphite mt-1 italic">
              基于 Isolation Forest（ML）检测 + Z-score 特征分析
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { fetchAnomalies, detectAnomalies } from '../api/index.js'

const props = defineProps({
  departmentId: { type: [Number, Object], default: null },
  year: { type: Number, default: 2025 },
})

const anomalies = ref([])
const loading = ref(false)
const detecting = ref(false)
const error = ref('')
const backendSummary = ref({})

const summaryText = computed(() => {
  return anomalies.value.length > 0
})

async function loadAnomalies() {
  loading.value = true
  error.value = ''
  try {
    const params = { year: props.year }
    if (props.departmentId) params.department_id = props.departmentId
    const res = await fetchAnomalies(params)
    anomalies.value = res.data || []
    backendSummary.value = res.summary || {}
  } catch (e) {
    console.error('加载异常失败:', e)
    error.value = '异常数据加载失败，请检查后端服务'
    anomalies.value = []
    backendSummary.value = {}
  } finally {
    loading.value = false
  }
}

async function runDetection() {
  if (detecting.value) return
  detecting.value = true
  error.value = ''
  try {
    // 触发异常检测（默认检测 6 月，因为这是种子数据有代表性的月份）
    const detectMonth = new Date().getMonth() + 1
    await detectAnomalies({
      year: props.year,
      month: detectMonth > 12 ? 12 : detectMonth,
      contamination: 0.15,
    })
    // 重新加载异常列表
    await loadAnomalies()
  } catch (e) {
    console.error('异常检测失败:', e)
    error.value = '异常检测失败: ' + (e.message || '请检查后端服务')
  } finally {
    detecting.value = false
  }
}

function severityLabel(s) {
  switch (s) {
    case 'high': return '高风险'
    case 'medium': return '中风险'
    case 'low': return '低风险'
    default: return s
  }
}

function severityBadgeClass(s) {
  switch (s) {
    case 'high': return 'bg-red-100 text-red-700'
    case 'medium': return 'bg-orange-100 text-orange-700'
    case 'low': return 'bg-yellow-100 text-yellow-700'
    default: return 'bg-gray-100 text-gray-600'
  }
}

function severityCardClass(s) {
  const base = 'p-3 rounded-lg border transition-colors'
  switch (s) {
    case 'high': return `${base} bg-red-50 border-red-200 hover:bg-red-100`
    case 'medium': return `${base} bg-orange-50 border-orange-200 hover:bg-orange-100`
    case 'low': return `${base} bg-yellow-50 border-yellow-200 hover:bg-yellow-100`
    default: return `${base} bg-gray-50 border-gray-200`
  }
}

function formatValue(val, metricName) {
  if (val == null) return '—'
  // 百分比类指标显示 %
  if (['gross_margin', 'profit_margin', 'cost_ratio'].includes(metricName)) {
    return val.toFixed(1) + '%'
  }
  return Number(val).toLocaleString('zh-CN', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }) + ' 万元'
}

onMounted(loadAnomalies)
watch(() => [props.departmentId, props.year], loadAnomalies)
</script>

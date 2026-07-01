<template>
  <div class="bg-white rounded-xl border border-gray-200 p-4">
    <h4 class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
      ⚠️ 异常预警
      <span
        v-if="summaryText"
        class="text-xs font-normal text-gray-400 ml-auto"
      >
        {{ summaryText }}
      </span>
    </h4>

    <!-- 加载中 -->
    <div v-if="loading" class="space-y-2">
      <div v-for="i in 3" :key="i" class="h-14 bg-gray-100 rounded-lg animate-pulse"></div>
    </div>

    <!-- 空状态 -->
    <div
      v-else-if="!anomalies.length"
      class="py-8 text-center text-gray-400 text-sm"
    >
      ✅ 未检测到异常
    </div>

    <!-- 异常列表 -->
    <div v-else class="space-y-2">
      <div
        v-for="a in anomalies"
        :key="a.id"
        :class="severityCardClass(a.severity)"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-0.5">
              <span
                :class="severityBadgeClass(a.severity)"
                class="px-1.5 py-0.5 rounded text-xs font-medium"
              >
                {{ severityLabel(a.severity) }}
              </span>
              <span class="text-sm font-medium text-gray-800">
                {{ a.metric_label }}
              </span>
              <span class="text-xs text-gray-400">
                {{ a.department_name }} · {{ a.year }}/{{ a.month }}
              </span>
            </div>
            <div class="flex items-center gap-3 text-xs mt-1">
              <span class="text-gray-600">
                实际值: <strong class="text-gray-800">{{ a.actual_value }}</strong>
              </span>
              <span class="text-gray-400">
                预期: {{ a.expected_range }}
              </span>
              <span
                :class="a.deviation_pct < 0 ? 'text-red-600' : 'text-amber-600'"
                class="font-medium"
              >
                {{ a.deviation_pct > 0 ? '+' : '' }}{{ a.deviation_pct.toFixed(1) }}%
              </span>
            </div>
            <div v-if="a.description" class="text-xs text-gray-500 mt-1 line-clamp-2">
              {{ a.description }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { fetchAnomalies } from '../api/index.js'

const props = defineProps({
  departmentId: { type: [Number, Object], default: null },
  year: { type: Number, default: 2025 },
})

const anomalies = ref([])
const loading = ref(false)

const summaryText = computed(() => {
  if (!anomalies.value.length) return ''
  const high = anomalies.value.filter(a => a.severity === 'high').length
  const medium = anomalies.value.filter(a => a.severity === 'medium').length
  const parts = []
  if (high) parts.push(`🔴${high}`)
  if (medium) parts.push(`🟠${medium}`)
  return parts.join(' ')
})

async function loadAnomalies() {
  loading.value = true
  try {
    const params = { year: props.year }
    if (props.departmentId) params.department_id = props.departmentId
    const res = await fetchAnomalies(params)
    anomalies.value = res.data || []
  } catch (e) {
    console.error('加载异常失败:', e)
    anomalies.value = []
  } finally {
    loading.value = false
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

onMounted(loadAnomalies)
watch(() => [props.departmentId, props.year], loadAnomalies)
</script>

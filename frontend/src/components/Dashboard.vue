<template>
  <div class="space-y-6">
    <!-- 加载错误 -->
    <div
      v-if="error"
      class="bg-yellow-50 border border-yellow-300 rounded-lg px-4 py-3 text-sm text-yellow-800 flex items-center gap-2"
    >
      <span class="text-base">⚠️</span>
      {{ error }}
    </div>

    <!-- KPI 卡片行 -->
    <KpiCards :indicators="indicators" :loading="loading" />

    <!-- 趋势图表 -->
    <TrendChart :indicators="indicators" :loading="loading" />

    <!-- 异常告警 -->
    <AnomalyAlert
      :department-id="departmentId"
      :year="year"
    />
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { fetchIndicators } from '../api/index.js'
import KpiCards from './KpiCards.vue'
import TrendChart from './TrendChart.vue'
import AnomalyAlert from './AnomalyAlert.vue'

const props = defineProps({
  departmentId: { type: [Number, Object], default: null },
  year: { type: Number, default: 2025 },
})

const indicators = ref([])
const loading = ref(false)
const error = ref('')

async function loadIndicators() {
  loading.value = true
  error.value = ''
  try {
    const params = { year: props.year }
    if (props.departmentId) params.department_id = props.departmentId
    const res = await fetchIndicators(params)
    indicators.value = res.data || []
  } catch (e) {
    console.error('加载指标失败:', e)
    error.value = '数据加载失败，请检查后端服务'
    indicators.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadIndicators)
watch(() => [props.departmentId, props.year], loadIndicators)
</script>

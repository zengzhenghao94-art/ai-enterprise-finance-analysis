<template>
  <div class="bg-white rounded-xl border border-gray-200 p-4">
    <h4 class="text-sm font-semibold text-gray-700 mb-3">📈 月度趋势</h4>

    <!-- 加载骨架 -->
    <div v-if="loading" class="h-64 bg-gray-100 rounded-lg animate-pulse"></div>

    <!-- 图表 -->
    <div v-else-if="indicators.length" ref="chartRef" class="h-64"></div>

    <!-- 空状态 -->
    <div v-else class="h-64 flex items-center justify-center text-gray-400 text-sm">
      暂无趋势数据
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  indicators: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const chartRef = ref(null)
let chart = null

function buildOption() {
  const data = [...props.indicators].sort((a, b) => {
    if (a.year !== b.year) return a.year - b.year
    return a.month - a.month
  })

  const xAxis = data.map(d => `${d.year}-${String(d.month).padStart(2, '0')}`)

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#fff',
      borderColor: '#e5e7eb',
      textStyle: { color: '#374151', fontSize: 12 },
    },
    legend: {
      data: ['营业收入', '营业成本', '净利润'],
      bottom: 0,
      textStyle: { fontSize: 11 },
    },
    grid: { left: 12, right: 12, top: 12, bottom: 36 },
    xAxis: {
      type: 'category',
      data: xAxis,
      axisLabel: { fontSize: 10, color: '#9ca3af', rotate: 45 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '万元',
      nameTextStyle: { fontSize: 10, color: '#9ca3af' },
      axisLabel: { fontSize: 10, color: '#9ca3af' },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series: [
      {
        name: '营业收入',
        type: 'line',
        data: data.map(d => d.revenue),
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: '#3b82f6', width: 2 },
        itemStyle: { color: '#3b82f6' },
      },
      {
        name: '营业成本',
        type: 'line',
        data: data.map(d => d.cost),
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: '#f59e0b', width: 2 },
        itemStyle: { color: '#f59e0b' },
      },
      {
        name: '净利润',
        type: 'line',
        data: data.map(d => d.net_profit),
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: '#10b981', width: 2 },
        itemStyle: { color: '#10b981' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.2)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.02)' },
          ]),
        },
      },
    ],
  }
}

function initOrUpdate() {
  if (!chartRef.value) return
  if (chart) {
    chart.setOption(buildOption(), { notMerge: true })
  } else {
    chart = echarts.init(chartRef.value)
    chart.setOption(buildOption())
  }
}

function handleResize() {
  chart?.resize()
}

watch(() => props.indicators, async () => {
  await nextTick()
  initOrUpdate()
})

onMounted(() => {
  initOrUpdate()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

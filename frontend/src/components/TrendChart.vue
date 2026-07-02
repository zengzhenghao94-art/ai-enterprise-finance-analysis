<template>
  <div class="bg-white rounded-xl border border-gray-200 p-4">
    <h4 class="text-sm font-semibold text-gray-700 mb-3">📈 月度趋势</h4>

    <!-- 加载骨架 -->
    <div v-if="loading" class="h-80 bg-gray-100 rounded-lg animate-pulse"></div>

    <!-- 图表 -->
    <div
      v-else-if="indicators.length"
      ref="chartRef"
      class="h-80 w-full"
    ></div>

    <!-- 空状态 -->
    <div v-else class="h-80 flex items-center justify-center text-gray-400 text-sm">
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

  // 判断是否为跨年数据，需要年份前缀区分同月
  const years = [...new Set(data.map(d => d.year))]
  const multiYear = years.length > 1

  const xAxisData = data.map(d =>
    multiYear ? `${d.year}/${d.month}月` : `${d.month}月`
  )

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#fff',
      borderColor: '#e5e7eb',
      textStyle: { color: '#374151', fontSize: 12 },
      formatter: function (params) {
        let html = `<strong>${params[0].axisValue}</strong><br/>`
        params.forEach(p => {
          html += `${p.marker} ${p.seriesName}: <strong>${p.value.toLocaleString('zh-CN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</strong> 万元<br/>`
        })
        return html
      },
    },
    legend: {
      data: ['营业收入', '营业成本', '净利润'],
      top: 0,
      left: 'center',
      textStyle: { fontSize: 11 },
      itemGap: 20,
    },
    grid: {
      left: 60,
      right: 24,
      top: 30,
      bottom: 40,
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      name: multiYear ? '年/月' : '月份',
      nameLocation: 'center',
      nameGap: 30,
      nameTextStyle: { fontSize: 11, color: '#6b7280' },
      axisLabel: {
        fontSize: 10,
        color: '#6b7280',
        interval: 1,
        rotate: data.length > 12 ? 30 : 0,
      },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '万元',
      nameLocation: 'end',
      nameGap: 10,
      nameTextStyle: { fontSize: 12, color: '#374151', fontWeight: 'bold', align: 'left' },
      axisLabel: {
        fontSize: 10,
        color: '#6b7280',
        formatter: v => v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v.toFixed(0),
      },
      splitNumber: 5,
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

function disposeChart() {
  if (chart) {
    chart.dispose()
    chart = null
  }
}

function renderChart() {
  if (!chartRef.value) return
  // 每次 render 前先 dispose 旧实例，确保绑定到当前 DOM
  disposeChart()
  chart = echarts.init(chartRef.value)
  chart.setOption(buildOption())
}

function handleResize() {
  chart?.resize()
}

// ⚠️ 关键：loading 变 true 时 v-if 会把 chart div 从 DOM 摘掉，
// 必须在此时 dispose ECharts 实例，否则之后 renderChart 拿到的是僵尸实例。
watch(() => props.loading, (newVal) => {
  if (newVal) {
    disposeChart()
  } else {
    nextTick().then(renderChart)
  }
})

// 非加载态下的数据更新（同部门切换月份等场景）
watch(() => props.indicators, () => {
  if (props.loading) return
  nextTick().then(() => {
    if (chart && chartRef.value) {
      chart.setOption(buildOption(), { notMerge: true })
      chart.resize()
    }
  })
})

onMounted(() => {
  if (!props.loading) {
    renderChart()
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  disposeChart()
})
</script>

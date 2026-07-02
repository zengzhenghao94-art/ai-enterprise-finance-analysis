<template>
  <div class="bg-white rounded-2xl border border-steep-dove p-4">
    <h4 class="text-sm font-semibold text-steep-ash mb-3">📈 月度趋势</h4>

    <!-- 加载骨架 -->
    <div v-if="loading" class="h-80 bg-steep-fog rounded-xl animate-pulse"></div>

    <!-- 图表 -->
    <div
      v-else-if="indicators.length"
      ref="chartRef"
      class="h-80 w-full"
    ></div>

    <!-- 空状态 -->
    <div v-else class="h-80 flex items-center justify-center text-steep-graphite text-sm">
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
      borderColor: '#a3a6af',
      textStyle: { color: '#17191c', fontSize: 12 },
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
      textStyle: { fontSize: 11, color: '#4c4c4c' },
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
      nameTextStyle: { fontSize: 11, color: '#777b86' },
      axisLabel: {
        fontSize: 10,
        color: '#777b86',
        interval: 1,
        rotate: data.length > 12 ? 30 : 0,
      },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#a3a6af' } },
    },
    yAxis: {
      type: 'value',
      name: '万元',
      nameLocation: 'end',
      nameGap: 10,
      nameTextStyle: { fontSize: 12, color: '#4c4c4c', fontWeight: 'bold', align: 'left' },
      axisLabel: {
        fontSize: 10,
        color: '#777b86',
        formatter: v => v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v.toFixed(0),
      },
      splitNumber: 5,
      splitLine: { lineStyle: { color: '#f7f7f8' } },
    },
    series: [
      {
        name: '营业收入',
        type: 'line',
        data: data.map(d => d.revenue),
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: '#1e40af', width: 2 },
        itemStyle: { color: '#1e40af' },
      },
      {
        name: '营业成本',
        type: 'line',
        data: data.map(d => d.cost),
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: '#0891b2', width: 2 },
        itemStyle: { color: '#0891b2' },
      },
      {
        name: '净利润',
        type: 'line',
        data: data.map(d => d.net_profit),
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: '#777b86', width: 2 },
        itemStyle: { color: '#777b86' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(119, 123, 134, 0.15)' },
            { offset: 1, color: 'rgba(119, 123, 134, 0.02)' },
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

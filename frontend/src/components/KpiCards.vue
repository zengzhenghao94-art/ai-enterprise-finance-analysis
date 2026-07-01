<template>
  <div>
    <!-- 加载骨架 -->
    <div v-if="loading" class="grid grid-cols-2 md:grid-cols-3 gap-4">
      <div v-for="i in 6" :key="i" class="bg-white rounded-xl p-4 border border-gray-200 animate-pulse">
        <div class="h-3 bg-gray-200 rounded w-16 mb-3"></div>
        <div class="h-6 bg-gray-200 rounded w-24"></div>
      </div>
    </div>

    <!-- 卡片网格 -->
    <div v-else class="grid grid-cols-2 md:grid-cols-3 gap-4">
      <div
        v-for="card in kpiList"
        :key="card.key"
        class="bg-white rounded-xl p-4 border border-gray-200 hover:shadow-md transition-shadow"
      >
        <div class="text-xs text-gray-400 mb-1">{{ card.label }}</div>
        <div class="text-xl font-bold text-gray-800">
          {{ formatNum(card.value) }}
          <span class="text-xs text-gray-400 font-normal">万元</span>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div
      v-if="!loading && !latestMonth"
      class="bg-white rounded-xl p-8 border border-gray-200 text-center text-gray-400 text-sm"
    >
      暂无指标数据
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  indicators: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

// 取最新月份的数据
const latestMonth = computed(() => {
  if (!props.indicators.length) return null
  const sorted = [...props.indicators].sort((a, b) => {
    if (a.year !== b.year) return b.year - a.year
    return b.month - a.month
  })
  return sorted[0]
})

const kpiList = computed(() => {
  const m = latestMonth.value
  if (!m) return []
  return [
    { key: 'revenue', label: '营业收入', value: m.revenue },
    { key: 'cost', label: '营业成本', value: m.cost },
    { key: 'net_profit', label: '净利润', value: m.net_profit },
    { key: 'operating_expense', label: '运营费用', value: m.operating_expense },
    { key: 'cash_flow', label: '经营现金流', value: m.cash_flow },
    { key: 'accounts_receivable', label: '应收账款', value: m.accounts_receivable },
  ]
})

function formatNum(v) {
  if (v == null) return '—'
  return Number(v).toLocaleString('zh-CN', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })
}
</script>

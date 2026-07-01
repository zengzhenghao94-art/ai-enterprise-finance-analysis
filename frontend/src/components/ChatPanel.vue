<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
    <!-- 标题栏 -->
    <div class="px-4 py-3 bg-blue-50 border-b border-blue-100">
      <h3 class="text-sm font-semibold text-blue-800 flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
        智能问数
      </h3>
    </div>

    <!-- 结果展示区 -->
    <div class="p-4 max-h-96 overflow-y-auto space-y-3" v-if="result">
      <!-- 生成的 SQL -->
      <div class="bg-gray-900 text-green-400 text-xs font-mono rounded-lg p-3 overflow-x-auto">
        <div class="text-gray-500 mb-1">📝 生成 SQL</div>
        {{ result.sql_generated }}
      </div>

      <!-- 数据表格 -->
      <div class="overflow-x-auto" v-if="result.result && result.result.length">
        <div class="text-xs text-gray-500 mb-1">📊 查询结果</div>
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
                {{ row[key] }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 自然语言解释 -->
      <div class="bg-blue-50 rounded-lg p-3 text-sm text-blue-900" v-if="result.explanation">
        <div class="text-xs text-blue-500 mb-1">💡 解读</div>
        {{ result.explanation }}
      </div>

      <!-- Token 消耗 -->
      <div class="text-xs text-gray-400 text-right" v-if="result.tokens_used">
        Token: {{ result.tokens_used }}
      </div>
    </div>

    <!-- 错误提示 -->
    <div class="px-4" v-if="error">
      <div class="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
        {{ error }}
      </div>
    </div>

    <!-- 输入区 -->
    <div class="px-4 py-3 border-t border-gray-100 flex gap-2">
      <input
        v-model="query"
        type="text"
        placeholder="输入问题，如：销售部今年收入是多少？"
        class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm
               focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        @keyup.enter="sendQuery"
      />
      <button
        @click="sendQuery"
        :disabled="loading || !query.trim()"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium
               hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
               transition-colors flex items-center gap-1"
      >
        <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span>{{ loading ? '查询中' : '发送' }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { queryNL2SQL } from '../api/index.js'

const props = defineProps({
  departmentId: { type: Number, default: null },
  year: { type: Number, default: 2025 },
})

const query = ref('')
const loading = ref(false)
const result = ref(null)
const error = ref('')

async function sendQuery() {
  if (!query.value.trim() || loading.value) return

  loading.value = true
  error.value = ''
  result.value = null

  try {
    const body = {
      query: query.value.trim(),
      department_id: props.departmentId ?? null,
      year: props.year,
    }
    result.value = await queryNL2SQL(body)
  } catch (e) {
    error.value = e.message || '查询失败，请检查后端服务是否正常运行'
  } finally {
    loading.value = false
  }
}
</script>

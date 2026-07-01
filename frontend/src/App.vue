<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 顶部导航 -->
    <NavBar
      :departments="departments"
      :selected-dept="selectedDept"
      :selected-year="selectedYear"
      @update:selected-dept="selectedDept = $event"
      @update:selected-year="selectedYear = $event"
    />

    <!-- 部门加载错误 -->
    <div
      v-if="deptError"
      class="max-w-7xl mx-auto px-4 pt-4"
    >
      <div class="bg-yellow-50 border border-yellow-300 rounded-lg px-4 py-3 text-sm text-yellow-800 flex items-center gap-2">
        <span>⚠️</span>
        {{ deptError }}
      </div>
    </div>

    <!-- 主体内容区：左右两栏 -->
    <main class="max-w-7xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 左栏：仪表盘（占 2/3） -->
      <section class="lg:col-span-2 space-y-6">
        <Dashboard
          :department-id="selectedDept"
          :year="selectedYear"
        />
      </section>

      <!-- 右栏：对话 + 简报（占 1/3） -->
      <aside class="space-y-6">
        <ChatPanel
          :department-id="selectedDept"
          :year="selectedYear"
        />
        <ReportPanel
          :department-id="selectedDept"
          :year="selectedYear"
        />
      </aside>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchDepartments } from './api/index.js'
import NavBar from './components/NavBar.vue'
import Dashboard from './components/Dashboard.vue'
import ChatPanel from './components/ChatPanel.vue'
import ReportPanel from './components/ReportPanel.vue'

const departments = ref([])
const selectedDept = ref(null)   // null = 全公司
const selectedYear = ref(2025)
const deptError = ref('')

onMounted(async () => {
  try {
    const res = await fetchDepartments()
    departments.value = res.data
  } catch (e) {
    console.error('加载部门列表失败:', e)
    deptError.value = '部门列表加载失败，请检查后端服务'
  }
})
</script>

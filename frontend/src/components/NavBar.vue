<template>
  <header class="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
      <!-- 左侧：Logo + 标题 -->
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
          <span class="text-white font-bold text-sm">AI</span>
        </div>
        <h1 class="text-lg font-semibold text-gray-800">经营分析平台</h1>
      </div>

      <!-- 右侧：部门选择 + 年份选择 -->
      <div class="flex items-center gap-4">
        <!-- 部门下拉 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-gray-500">部门</label>
          <select
            :value="selectedDept"
            @change="$emit('update:selected-dept', $event.target.value ? Number($event.target.value) : null)"
            class="px-3 py-1.5 border border-gray-300 rounded-md text-sm
                   focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none
                   bg-white cursor-pointer"
          >
            <option :value="null">全公司</option>
            <option
              v-for="d in departments"
              :key="d.id"
              :value="d.id"
            >
              {{ d.name }}
            </option>
          </select>
        </div>

        <!-- 年份选择 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-gray-500">年份</label>
          <select
            :value="selectedYear"
            @change="$emit('update:selected-year', Number($event.target.value))"
            class="px-3 py-1.5 border border-gray-300 rounded-md text-sm
                   focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none
                   bg-white cursor-pointer"
          >
            <option :value="2024">2024</option>
            <option :value="2025">2025</option>
            <option :value="2026">2026</option>
          </select>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
defineProps({
  departments: { type: Array, default: () => [] },
  selectedDept: { type: Number, default: null },
  selectedYear: { type: Number, default: 2025 },
})

defineEmits(['update:selected-dept', 'update:selected-year'])
</script>

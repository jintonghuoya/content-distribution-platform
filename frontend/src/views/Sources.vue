<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>数据源管理</span>
          <el-button type="primary" :loading="collecting" @click="handleCollect">
            <el-icon><Refresh /></el-icon> 立即采集
          </el-button>
        </div>
      </template>

      <el-table :data="sources" v-loading="loading" stripe>
        <el-table-column prop="source" label="来源标识" width="150" />
        <el-table-column prop="name" label="来源名称" min-width="200" />
        <el-table-column label="采集间隔" width="150">
          <template #default="{ row }">
            {{ row.interval_seconds ? `${row.interval_seconds / 60} 分钟` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="状态" width="120">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              :loading="toggleLoading === row.source"
              @change="(v: boolean) => handleToggle(row, v)"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSources, toggleSource, collectTopics } from '@/api/sources'
import type { SourceInfo } from '@/types'

const sources = ref<SourceInfo[]>([])
const loading = ref(false)
const collecting = ref(false)
const toggleLoading = ref<string | null>(null)

async function fetchSources() {
  loading.value = true
  try {
    const res = await getSources()
    sources.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleToggle(row: SourceInfo, enabled: boolean) {
  toggleLoading.value = row.source
  try {
    await toggleSource(row.source, enabled)
    ElMessage.success(`${row.name} 已${enabled ? '启用' : '禁用'}`)
  } catch {
    row.enabled = !enabled // revert on error
  } finally {
    toggleLoading.value = null
  }
}

async function handleCollect() {
  collecting.value = true
  try {
    const res = await collectTopics()
    ElMessage.success(res.data.message || '采集完成')
  } finally {
    collecting.value = false
  }
}

onMounted(fetchSources)
</script>

<style scoped lang="scss">
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}
</style>

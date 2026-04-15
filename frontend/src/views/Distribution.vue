<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>分发记录</span>
          <el-button type="primary" :loading="batchLoading" @click="handleBatchDistribute">
            <el-icon><Refresh /></el-icon> 批量分发
          </el-button>
        </div>
      </template>

      <!-- Filter bar -->
      <el-form :inline="true" class="filter-bar">
        <el-form-item label="平台">
          <el-select v-model="filters.platform" clearable placeholder="全部" @change="fetchRecords">
            <el-option label="微博" value="weibo" />
            <el-option label="微信" value="wechat" />
            <el-option label="头条" value="toutiao" />
            <el-option label="小红书" value="xiaohongshu" />
            <el-option label="B站" value="bilibili" />
            <el-option label="抖音" value="douyin" />
          </el-select>
        </el-form-item>
      </el-form>

      <el-table :data="records" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="content_id" label="内容ID" width="100" />
        <el-table-column prop="platform" label="平台" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ platformLabel(row.platform) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="success" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'" size="small">
              {{ row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="platform_url" label="发布链接" min-width="200">
          <template #default="{ row }">
            <el-link v-if="row.platform_url" :href="row.platform_url" target="_blank" type="primary">
              查看
            </el-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip min-width="200" />
        <el-table-column prop="published_at" label="发布时间" width="180">
          <template #default="{ row }">{{ formatTime(row.published_at) }}</template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchRecords"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getDistributionRecords, triggerDistributeAll } from '@/api/distributors'
import type { DistributionRecord } from '@/types'

const records = ref<DistributionRecord[]>([])
const loading = ref(false)
const batchLoading = ref(false)
const total = ref(0)
const page = ref(1)
const size = ref(20)
const filters = ref({ platform: '' })

function platformLabel(p: string) {
  const map: Record<string, string> = {
    weibo: '微博', wechat: '微信', toutiao: '头条',
    xiaohongshu: '小红书', bilibili: 'B站', douyin: '抖音',
  }
  return map[p] || p
}

function formatTime(t: string) {
  return new Date(t).toLocaleString('zh-CN')
}

async function fetchRecords() {
  loading.value = true
  try {
    const params: any = { page: page.value, size: size.value }
    if (filters.value.platform) params.platform = filters.value.platform
    const res = await getDistributionRecords(params)
    records.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleBatchDistribute() {
  batchLoading.value = true
  try {
    const res = await triggerDistributeAll()
    ElMessage.success(res.data.message || '批量分发已触发')
    await fetchRecords()
  } finally {
    batchLoading.value = false
  }
}

onMounted(fetchRecords)
</script>

<style scoped lang="scss">
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.filter-bar { margin-bottom: 16px; }

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>

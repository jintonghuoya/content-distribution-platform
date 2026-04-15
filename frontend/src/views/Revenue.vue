<template>
  <div class="page-container">
    <!-- Summary cards -->
    <el-row :gutter="16" class="summary-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="总收益 (元)" :value="summary.total_revenue" :precision="2" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="总浏览量" :value="summary.total_views" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="总点赞" :value="summary.total_likes" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="总互动" :value="summary.total_engagement" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Revenue chart -->
    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <div class="card-header">
          <span style="font-weight: 600">收益趋势</span>
          <el-button type="primary" :loading="collectLoading" @click="handleCollect">
            <el-icon><Refresh /></el-icon> 采集收益
          </el-button>
        </div>
      </template>
      <v-chart :option="chartOption" style="height: 300px" autoresize />
    </el-card>

    <!-- Revenue records table -->
    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <span style="font-weight: 600">收益明细</span>
      </template>

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
        <el-table-column prop="platform" label="平台" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ platformLabel(row.platform) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content_id" label="内容ID" width="90" />
        <el-table-column prop="views" label="浏览" width="100" sortable />
        <el-table-column prop="likes" label="点赞" width="80" sortable />
        <el-table-column prop="comments" label="评论" width="80" />
        <el-table-column prop="shares" label="分享" width="80" />
        <el-table-column prop="revenue_amount" label="收益(元)" width="110" sortable>
          <template #default="{ row }">
            <span style="color: #67c23a; font-weight: 600">¥{{ row.revenue_amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="recorded_at" label="记录时间" width="180">
          <template #default="{ row }">{{ formatTime(row.recorded_at) }}</template>
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
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { getRevenueRecords, getRevenueSummary, triggerRevenueCollect } from '@/api/revenue'
import type { RevenueRecord } from '@/types'

use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent])

const records = ref<RevenueRecord[]>([])
const loading = ref(false)
const collectLoading = ref(false)
const total = ref(0)
const page = ref(1)
const size = ref(20)
const filters = ref({ platform: '' })

const summary = reactive({
  total_revenue: 0,
  total_views: 0,
  total_likes: 0,
  total_engagement: 0,
})

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

const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['收益', '浏览量'] },
  xAxis: { type: 'category', data: records.value.slice(0, 10).map(r => r.date || r.recorded_at?.slice(0, 10)) },
  yAxis: [
    { type: 'value', name: '收益(元)' },
    { type: 'value', name: '浏览量' },
  ],
  series: [
    {
      name: '收益',
      type: 'bar',
      data: records.value.slice(0, 10).map(r => r.revenue_amount),
      itemStyle: { color: '#67c23a' },
    },
    {
      name: '浏览量',
      type: 'line',
      yAxisIndex: 1,
      data: records.value.slice(0, 10).map(r => r.views),
      itemStyle: { color: '#409eff' },
    },
  ],
}))

async function fetchRecords() {
  loading.value = true
  try {
    const params: any = { page: page.value, size: size.value }
    if (filters.value.platform) params.platform = filters.value.platform
    const res = await getRevenueRecords(params)
    records.value = res.data
  } finally {
    loading.value = false
  }
}

async function fetchSummary() {
  try {
    const res = await getRevenueSummary()
    Object.assign(summary, res.data)
  } catch {
    // no data yet
  }
}

async function handleCollect() {
  collectLoading.value = true
  try {
    await triggerRevenueCollect()
    ElMessage.success('收益采集已触发')
    await fetchRecords()
    await fetchSummary()
  } finally {
    collectLoading.value = false
  }
}

onMounted(() => {
  fetchRecords()
  fetchSummary()
})
</script>

<style scoped lang="scss">
.summary-row { margin-bottom: 0; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar { margin-bottom: 16px; }

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>

<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>话题管理</span>
          <el-button type="primary" :loading="collecting" @click="handleCollect">
            <el-icon><Refresh /></el-icon> 立即采集
          </el-button>
        </div>
      </template>

      <!-- Filter bar -->
      <el-form :inline="true" class="filter-bar">
        <el-form-item label="来源">
          <el-select v-model="filters.source" clearable placeholder="全部" @change="fetchTopics">
            <el-option v-for="s in sourceOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" @change="fetchTopics">
            <el-option label="待过滤" value="pending" />
            <el-option label="已过滤" value="filtered" />
            <el-option label="已拒绝" value="rejected" />
            <el-option label="生成中" value="generating" />
            <el-option label="已发布" value="published" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="fetchTopics">
            <el-icon><Search /></el-icon> 查询
          </el-button>
        </el-form-item>
      </el-form>

      <!-- Data table -->
      <el-table :data="topics" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" show-overflow-tooltip min-width="300" />
        <el-table-column prop="source" label="来源" width="100" />
        <el-table-column prop="heat_value" label="热度" width="100" sortable />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="collected_at" label="采集时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.collected_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showDetail(row)">详情</el-button>
            <el-button
              v-if="row.status === 'pending'"
              link type="warning" size="small"
              :loading="actionLoading === row.id + '-filter'"
              @click="handleFilterTopic(row)"
            >
              过滤
            </el-button>
            <el-button
              v-if="row.status === 'filtered'"
              link type="success" size="small"
              :loading="actionLoading === row.id + '-generate'"
              @click="handleGenerateTopic(row)"
            >
              生成
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchTopics"
          @current-change="fetchTopics"
        />
      </div>
    </el-card>

    <!-- Detail drawer -->
    <el-drawer v-model="drawerVisible" title="话题详情" size="500px">
      <template v-if="detailData">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="ID">{{ detailData.id }}</el-descriptions-item>
          <el-descriptions-item label="标题">{{ detailData.title }}</el-descriptions-item>
          <el-descriptions-item label="来源">{{ detailData.source }}</el-descriptions-item>
          <el-descriptions-item label="来源ID">{{ detailData.source_id }}</el-descriptions-item>
          <el-descriptions-item label="排名">{{ detailData.rank }}</el-descriptions-item>
          <el-descriptions-item label="热度">{{ detailData.heat_value }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ detailData.category }}</el-descriptions-item>
          <el-descriptions-item label="优先级">{{ detailData.priority }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType(detailData.status)" size="small">
              {{ statusLabel(detailData.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="采集时间">{{ formatTime(detailData.collected_at) }}</el-descriptions-item>
          <el-descriptions-item label="来源链接">
            <el-link :href="detailData.source_url" target="_blank" type="primary">
              {{ detailData.source_url }}
            </el-link>
          </el-descriptions-item>
        </el-descriptions>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getTopics, getTopic } from '@/api/topics'
import { collectTopics } from '@/api/sources'
import { triggerFilterTopic } from '@/api/filters'
import { triggerGenerateTopic } from '@/api/generators'
import type { Topic } from '@/types'

const topics = ref<Topic[]>([])
const loading = ref(false)
const collecting = ref(false)
const actionLoading = ref<string | null>(null)
const total = ref(0)
const page = ref(1)
const size = ref(20)

const filters = ref({ source: '', status: '' })
const sourceOptions = ['weibo', 'baidu', 'zhihu', 'douyin', 'bilibili', 'toutiao']

const drawerVisible = ref(false)
const detailData = ref<Topic | null>(null)

function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '待过滤', filtered: '已过滤', rejected: '已拒绝',
    generating: '生成中', published: '已发布',
  }
  return map[status] || status
}

function statusTagType(status: string) {
  const map: Record<string, string> = {
    pending: 'info', filtered: 'success', rejected: 'danger',
    generating: 'warning', published: '',
  }
  return (map[status] || 'info') as any
}

function formatTime(t: string) {
  return new Date(t).toLocaleString('zh-CN')
}

async function fetchTopics() {
  loading.value = true
  try {
    const params: any = { page: page.value, size: size.value }
    if (filters.value.source) params.source = filters.value.source
    if (filters.value.status) params.status = filters.value.status
    const res = await getTopics(params)
    topics.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function handleCollect() {
  collecting.value = true
  try {
    const res = await collectTopics()
    ElMessage.success(res.data.message || '采集完成')
    await fetchTopics()
  } finally {
    collecting.value = false
  }
}

async function handleFilterTopic(row: Topic) {
  actionLoading.value = row.id + '-filter'
  try {
    const res = await triggerFilterTopic(row.id)
    ElMessage.success(`过滤完成：${res.data.filtered ? '通过' : '已拒绝'}`)
    await fetchTopics()
  } finally {
    actionLoading.value = null
  }
}

async function handleGenerateTopic(row: Topic) {
  actionLoading.value = row.id + '-generate'
  try {
    await triggerGenerateTopic(row.id)
    ElMessage.success('内容生成已触发')
    await fetchTopics()
  } finally {
    actionLoading.value = null
  }
}

async function showDetail(row: Topic) {
  const res = await getTopic(row.id)
  detailData.value = res.data
  drawerVisible.value = true
}

onMounted(fetchTopics)
</script>

<style scoped lang="scss">
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.filter-bar {
  margin-bottom: 16px;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>

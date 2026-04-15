<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>内容管理</span>
          <el-button type="primary" :loading="batchLoading" @click="handleBatchGenerate">
            <el-icon><Refresh /></el-icon> 批量生成
          </el-button>
        </div>
      </template>

      <!-- Filter bar -->
      <el-form :inline="true" class="filter-bar">
        <el-form-item label="类型">
          <el-select v-model="filters.content_type" clearable placeholder="全部" @change="fetchContent">
            <el-option label="文章" value="article" />
            <el-option label="社交帖子" value="social_post" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" @change="fetchContent">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
          </el-select>
        </el-form-item>
      </el-form>

      <el-table :data="contents" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" show-overflow-tooltip min-width="300" />
        <el-table-column prop="content_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.content_type === 'article' ? '' : 'warning'">
              {{ row.content_type === 'article' ? '文章' : '社交帖子' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="topic_id" label="话题ID" width="90" />
        <el-table-column prop="llm_model" label="模型" width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
              {{ row.status === 'draft' ? '草稿' : '已发布' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showPreview(row)">预览</el-button>
            <el-popconfirm
              v-if="row.status === 'draft'"
              title="确定发布此内容？"
              @confirm="handlePublish(row)"
            >
              <template #reference>
                <el-button link type="success" size="small">发布</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          :page-sizes="[20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchContent"
          @current-change="fetchContent"
        />
      </div>
    </el-card>

    <!-- Preview drawer -->
    <el-drawer v-model="drawerVisible" title="内容预览" size="600px">
      <template v-if="previewData">
        <h2>{{ previewData.title }}</h2>
        <el-descriptions :column="2" border size="small" style="margin: 16px 0">
          <el-descriptions-item label="类型">{{ previewData.content_type }}</el-descriptions-item>
          <el-descriptions-item label="模型">{{ previewData.llm_model }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ previewData.status }}</el-descriptions-item>
          <el-descriptions-item label="Prompt">{{ previewData.prompt_name }}</el-descriptions-item>
        </el-descriptions>
        <el-divider />
        <div class="content-body" v-html="previewData.body"></div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getGeneratedContent, publishContent, triggerGenerateAll, getGeneratedContentDetail } from '@/api/generators'
import type { GeneratedContent } from '@/types'

const contents = ref<GeneratedContent[]>([])
const loading = ref(false)
const batchLoading = ref(false)
const total = ref(0)
const page = ref(1)
const size = ref(20)
const filters = ref({ content_type: '', status: '' })

const drawerVisible = ref(false)
const previewData = ref<GeneratedContent | null>(null)

function formatTime(t: string) {
  return new Date(t).toLocaleString('zh-CN')
}

async function fetchContent() {
  loading.value = true
  try {
    const params: any = { page: page.value, size: size.value }
    if (filters.value.content_type) params.content_type = filters.value.content_type
    if (filters.value.status) params.status = filters.value.status
    const res = await getGeneratedContent(params)
    contents.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function handleBatchGenerate() {
  batchLoading.value = true
  try {
    const res = await triggerGenerateAll()
    ElMessage.success(res.data.message || '生成任务已提交，后台执行中')
  } finally {
    batchLoading.value = false
  }
}

async function handlePublish(row: GeneratedContent) {
  await publishContent(row.id)
  ElMessage.success('已发布')
  await fetchContent()
}

async function showPreview(row: GeneratedContent) {
  const res = await getGeneratedContentDetail(row.id)
  previewData.value = res.data
  drawerVisible.value = true
}

onMounted(fetchContent)
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

.content-body {
  line-height: 1.8;
  font-size: 14px;

  :deep(img) { max-width: 100%; }
}
</style>

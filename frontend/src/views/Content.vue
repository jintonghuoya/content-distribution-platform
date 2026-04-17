<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>内容管理</span>
          <div class="header-actions">
            <el-button type="primary" :loading="batchGenerateLoading" @click="handleBatchGenerate">
              <el-icon><Refresh /></el-icon> 批量生成
            </el-button>
            <el-button
              type="success"
              :disabled="selectedIds.length === 0"
              @click="showDistributeDialog"
            >
              <el-icon><Promotion /></el-icon> 批量分发 ({{ selectedIds.length }})
            </el-button>
          </div>
        </div>
      </template>

      <!-- Filter bar -->
      <el-form :inline="true" class="filter-bar">
        <el-form-item label="类型">
          <el-select v-model="filters.content_type" clearable placeholder="全部" @change="handleFilterChange">
            <el-option label="文章" value="article" />
            <el-option label="社交帖子" value="social_post" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" @change="handleFilterChange">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
          </el-select>
        </el-form-item>
        <el-form-item label="话题ID">
          <el-input v-model="filters.topic_id" placeholder="输入话题ID" clearable style="width: 120px" @change="handleFilterChange" />
        </el-form-item>
        <el-form-item>
          <el-button @click="handleFilterChange">
            <el-icon><Search /></el-icon> 查询
          </el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- Batch action bar (shown when items selected) -->
      <div v-if="selectedIds.length > 0" class="batch-bar">
        <span>已选择 <b>{{ selectedIds.length }}</b> 条内容</span>
        <el-button size="small" @click="clearSelection">取消选择</el-button>
      </div>

      <el-table
        :data="contents"
        v-loading="loading"
        stripe
        @selection-change="handleSelectionChange"
        ref="tableRef"
      >
        <el-table-column type="selection" width="50" />
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
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showPreview(row)">预览</el-button>
            <el-button
              v-if="row.status === 'draft'"
              link type="success" size="small"
              @click="distributeSingle(row)"
            >
              分发
            </el-button>
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
          <el-descriptions-item label="话题ID">{{ previewData.topic_id }}</el-descriptions-item>
        </el-descriptions>
        <el-divider />
        <div class="content-body" v-html="previewData.body"></div>
        <el-divider />
        <el-button type="success" @click="distributeSingle(previewData!)">
          <el-icon><Promotion /></el-icon> 分发到平台
        </el-button>
      </template>
    </el-drawer>

    <!-- Distribute dialog -->
    <el-dialog v-model="distributeDialogVisible" title="选择分发平台" width="400px">
      <el-checkbox-group v-model="selectedPlatforms">
        <el-checkbox v-for="p in availablePlatforms" :key="p.value" :value="p.value" :label="p.label">
          {{ p.label }}
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="distributeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="distributing" @click="handleDistribute">
          确认分发 ({{ distributeTargetCount }} 条)
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getGeneratedContent, triggerGenerateAll, getGeneratedContentDetail } from '@/api/generators'
import { triggerDistributeContent } from '@/api/distributors'
import type { GeneratedContent } from '@/types'

const contents = ref<GeneratedContent[]>([])
const loading = ref(false)
const batchGenerateLoading = ref(false)
const distributing = ref(false)
const total = ref(0)
const page = ref(1)
const size = ref(20)
const filters = ref({ content_type: '', status: '', topic_id: '' })
const tableRef = ref()

const selectedIds = ref<number[]>([])
const selectedRows = ref<GeneratedContent[]>([])

const drawerVisible = ref(false)
const previewData = ref<GeneratedContent | null>(null)

const distributeDialogVisible = ref(false)
const selectedPlatforms = ref<string[]>(['weibo'])
const distributeTargetIds = ref<number[]>([])

const availablePlatforms = [
  { value: 'weibo', label: '微博' },
  { value: 'wechat', label: '微信公众号' },
  { value: 'toutiao', label: '今日头条' },
  { value: 'xiaohongshu', label: '小红书' },
  { value: 'bilibili', label: 'B站' },
  { value: 'douyin', label: '抖音' },
]

const distributeTargetCount = computed(() => distributeTargetIds.value.length * selectedPlatforms.value.length)

function formatTime(t: string) {
  return new Date(t).toLocaleString('zh-CN')
}

function handleSelectionChange(rows: GeneratedContent[]) {
  selectedRows.value = rows
  selectedIds.value = rows.map(r => r.id)
}

function clearSelection() {
  tableRef.value?.clearSelection()
}

function handleFilterChange() {
  page.value = 1
  fetchContent()
}

function resetFilters() {
  filters.value = { content_type: '', status: '', topic_id: '' }
  handleFilterChange()
}

async function fetchContent() {
  loading.value = true
  try {
    const params: any = { page: page.value, size: size.value }
    if (filters.value.content_type) params.content_type = filters.value.content_type
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.topic_id) params.topic_id = Number(filters.value.topic_id)
    params.exclude_published = true
    const res = await getGeneratedContent(params)
    contents.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function handleBatchGenerate() {
  batchGenerateLoading.value = true
  try {
    const res = await triggerGenerateAll()
    ElMessage.success(res.data.message || '生成任务已提交，后台执行中')
  } finally {
    batchGenerateLoading.value = false
  }
}

async function showPreview(row: GeneratedContent) {
  const res = await getGeneratedContentDetail(row.id)
  previewData.value = res.data
  drawerVisible.value = true
}

function showDistributeDialog() {
  distributeTargetIds.value = selectedIds.value.slice()
  distributeDialogVisible.value = true
}

async function distributeSingle(row: GeneratedContent) {
  distributeTargetIds.value = [row.id]
  distributeDialogVisible.value = true
}

async function handleDistribute() {
  if (selectedPlatforms.value.length === 0) {
    ElMessage.warning('请至少选择一个平台')
    return
  }

  distributing.value = true
  distributeDialogVisible.value = false
  let success = 0
  let fail = 0

  try {
    for (const contentId of distributeTargetIds.value) {
      for (const platform of selectedPlatforms.value) {
        try {
          await triggerDistributeContent(contentId, platform)
          success++
        } catch {
          fail++
        }
      }
    }
    if (fail === 0) {
      ElMessage.success(`已提交 ${success} 条分发任务`)
    } else {
      ElMessage.warning(`分发完成：成功 ${success}，失败 ${fail}`)
    }
    clearSelection()
    await fetchContent()
  } finally {
    distributing.value = false
  }
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

.header-actions {
  display: flex;
  gap: 8px;
}

.filter-bar { margin-bottom: 16px; }

.batch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  margin-bottom: 12px;
  background: #ecf5ff;
  border-radius: 4px;
  border: 1px solid #d9ecff;
}

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

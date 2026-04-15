<template>
  <div class="page-container">
    <!-- Pipeline stats cards -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="4.8" v-for="stage in pipelineStages" :key="stage.key">
        <el-card shadow="hover" class="stat-card">
          <el-statistic :title="stage.label" :value="stage.count" />
          <div class="stat-footer">
            <el-tag :type="stage.tagType" size="small">{{ stage.tag }}</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Pipeline trigger buttons -->
    <el-card shadow="never" class="pipeline-card">
      <template #header>
        <span style="font-weight: 600">流水线操作</span>
      </template>
      <div class="pipeline-actions">
        <div class="pipeline-step" v-for="step in pipelineSteps" :key="step.key">
          <el-button
            :type="step.type"
            :loading="step.loading"
            size="large"
            @click="handleTrigger(step)"
          >
            <el-icon :size="20"><component :is="step.icon" /></el-icon>
            <span style="margin-left: 6px">{{ step.label }}</span>
          </el-button>
          <div class="step-desc">{{ step.desc }}</div>
        </div>
        <div class="pipeline-arrow" v-for="i in 4" :key="'arrow-' + i">
          <el-icon :size="24" color="#c0c4cc"><ArrowRight /></el-icon>
        </div>
      </div>
    </el-card>

    <!-- Recent topics -->
    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <div class="card-header">
          <span style="font-weight: 600">最近话题</span>
          <el-button link type="primary" @click="$router.push('/topics')">查看全部</el-button>
        </div>
      </template>
      <el-table :data="recentTopics" v-loading="topicsLoading" stripe size="small">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" show-overflow-tooltip />
        <el-table-column prop="source" label="来源" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="collected_at" label="采集时间" width="180">
          <template #default="{ row }">{{ formatTime(row.collected_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getTopics } from '@/api/topics'
import { collectTopics } from '@/api/sources'
import { triggerFilterAll } from '@/api/filters'
import { triggerGenerateAll } from '@/api/generators'
import { triggerDistributeAll } from '@/api/distributors'
import { triggerRevenueCollect } from '@/api/revenue'
import type { Topic } from '@/types'

const recentTopics = ref<Topic[]>([])
const topicsLoading = ref(false)

const pipelineStages = reactive([
  { key: 'pending', label: '待过滤', count: 0, tag: '采集阶段', tagType: 'info' as const },
  { key: 'filtered', label: '已过滤', count: 0, tag: '过滤完成', tagType: 'success' as const },
  { key: 'generating', label: '生成中', count: 0, tag: '内容生成', tagType: 'warning' as const },
  { key: 'published', label: '已发布', count: 0, tag: '已分发', tagType: '' as const },
  { key: 'rejected', label: '已拒绝', count: 0, tag: '过滤拒绝', tagType: 'danger' as const },
])

const pipelineSteps = reactive([
  { key: 'collect', label: '采集', desc: '从各平台抓取热点', icon: 'Download', type: 'primary' as const, loading: false, action: collectTopics },
  { key: 'filter', label: '过滤', desc: '规则+LLM过滤', icon: 'Filter', type: 'success' as const, loading: false, action: triggerFilterAll },
  { key: 'generate', label: '生成', desc: 'AI生成文章内容', icon: 'EditPen', type: 'warning' as const, loading: false, action: triggerGenerateAll },
  { key: 'distribute', label: '分发', desc: '发布到各平台', icon: 'Promotion', type: 'danger' as const, loading: false, action: triggerDistributeAll },
  { key: 'revenue', label: '收益', desc: '采集收益数据', icon: 'Money', type: 'info' as const, loading: false, action: triggerRevenueCollect },
])

function statusLabel(status: string) {
  const map: Record<string, string> = { pending: '待过滤', filtered: '已过滤', rejected: '已拒绝', generating: '生成中', published: '已发布' }
  return map[status] || status
}

function statusTagType(status: string) {
  const map: Record<string, string> = { pending: 'info', filtered: 'success', rejected: 'danger', generating: 'warning', published: '' }
  return (map[status] || 'info') as any
}

function formatTime(t: string) {
  return new Date(t).toLocaleString('zh-CN')
}

async function fetchStats() {
  for (const stage of pipelineStages) {
    try {
      const res = await getTopics({ status: stage.key, size: 1 })
      stage.count = res.data.total
    } catch {
      // skip on error
    }
  }
}

async function fetchRecentTopics() {
  topicsLoading.value = true
  try {
    const res = await getTopics({ size: 10 })
    recentTopics.value = res.data.items
  } catch {
    // skip on error
  } finally {
    topicsLoading.value = false
  }
}

async function handleTrigger(step: typeof pipelineSteps[0]) {
  step.loading = true
  try {
    const res = await step.action()
    ElMessage.success(res.data?.message || `${step.label}已触发`)
    await fetchStats()
    await fetchRecentTopics()
  } finally {
    step.loading = false
  }
}

onMounted(() => {
  fetchStats()
  fetchRecentTopics()
})
</script>

<style scoped lang="scss">
.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
}

.stat-footer {
  margin-top: 8px;
}

.pipeline-card {
  .pipeline-actions {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 16px 0;
  }

  .pipeline-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }

  .step-desc {
    font-size: 12px;
    color: #909399;
  }

  .pipeline-arrow {
    display: flex;
    align-items: center;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>

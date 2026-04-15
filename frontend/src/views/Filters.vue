<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>过滤规则</span>
          <div>
            <el-button type="primary" @click="openCreateDialog">
              <el-icon><Plus /></el-icon> 新增规则
            </el-button>
            <el-button type="success" :loading="triggerLoading" @click="handleTriggerAll">
              <el-icon><Refresh /></el-icon> 全量过滤
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="rules" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="规则名称" min-width="200" />
        <el-table-column prop="rule_type" label="类型" width="160">
          <template #default="{ row }">
            <el-tag size="small">{{ ruleTypeLabel(row.rule_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="config" label="配置" min-width="250">
          <template #default="{ row }">
            <code style="font-size: 12px">{{ formatConfig(row.config) }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="启用" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="handleToggleEnabled(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="run_order" label="执行顺序" width="100" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm title="确定删除此规则？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create/Edit dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑规则' : '新增规则'" width="560px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="规则名称">
          <el-input v-model="form.name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="规则类型">
          <el-select v-model="form.rule_type" @change="onRuleTypeChange">
            <el-option label="关键词黑名单" value="keyword_blacklist" />
            <el-option label="热度阈值" value="heat_threshold" />
            <el-option label="来源权重" value="source_weight" />
          </el-select>
        </el-form-item>

        <!-- Dynamic config fields -->
        <template v-if="form.rule_type === 'keyword_blacklist'">
          <el-form-item label="关键词">
            <el-select
              v-model="configKeywords"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="输入关键词后回车添加"
              style="width: 100%"
            />
          </el-form-item>
        </template>

        <template v-else-if="form.rule_type === 'heat_threshold'">
          <el-form-item label="最低热度">
            <el-input-number v-model="configMinHeat" :min="0" />
          </el-form-item>
          <el-form-item label="最高热度">
            <el-input-number v-model="configMaxHeat" :min="0" />
          </el-form-item>
        </template>

        <template v-else-if="form.rule_type === 'source_weight'">
          <el-form-item label="来源权重">
            <div v-for="(weight, source) in configWeights" :key="source" class="weight-row">
              <span>{{ source }}</span>
              <el-input-number
                :model-value="weight"
                :min="0" :max="10" :step="0.1"
                @update:model-value="(v: number) => configWeights[source] = v"
              />
            </div>
          </el-form-item>
        </template>

        <el-form-item label="执行顺序">
          <el-input-number v-model="form.run_order" :min="0" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getFilterRules, createFilterRule, updateFilterRule, deleteFilterRule, triggerFilterAll } from '@/api/filters'
import type { FilterRule } from '@/types'

const rules = ref<FilterRule[]>([])
const loading = ref(false)
const triggerLoading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)

const form = ref({
  name: '',
  rule_type: 'keyword_blacklist',
  config: {} as Record<string, any>,
  enabled: true,
  run_order: 0,
})

// Dynamic config fields
const configKeywords = ref<string[]>([])
const configMinHeat = ref(100)
const configMaxHeat = ref(1000000)
const configWeights = ref<Record<string, number>>({ weibo: 1.0, baidu: 0.8, zhihu: 1.2 })

function ruleTypeLabel(type: string) {
  const map: Record<string, string> = {
    keyword_blacklist: '关键词黑名单',
    heat_threshold: '热度阈值',
    source_weight: '来源权重',
  }
  return map[type] || type
}

function formatConfig(config: Record<string, any>) {
  if (!config) return '-'
  if (config.keywords) return `关键词: ${config.keywords.join(', ')}`
  if (config.min_heat !== undefined) return `热度: ${config.min_heat} ~ ${config.max_heat}`
  if (config.weights) return Object.entries(config.weights).map(([k, v]) => `${k}:${v}`).join(', ')
  return JSON.stringify(config)
}

function buildConfig(): Record<string, any> {
  if (form.value.rule_type === 'keyword_blacklist') {
    return { keywords: configKeywords.value }
  }
  if (form.value.rule_type === 'heat_threshold') {
    return { min_heat: configMinHeat.value, max_heat: configMaxHeat.value }
  }
  if (form.value.rule_type === 'source_weight') {
    return { weights: configWeights.value }
  }
  return {}
}

function onRuleTypeChange() {
  // Reset config fields when type changes
}

function openCreateDialog() {
  isEdit.value = false
  editId.value = null
  form.value = { name: '', rule_type: 'keyword_blacklist', config: {}, enabled: true, run_order: 0 }
  configKeywords.value = []
  configMinHeat.value = 100
  configMaxHeat.value = 1000000
  configWeights.value = { weibo: 1.0, baidu: 0.8, zhihu: 1.2 }
  dialogVisible.value = true
}

function openEditDialog(row: FilterRule) {
  isEdit.value = true
  editId.value = row.id
  form.value = {
    name: row.name,
    rule_type: row.rule_type,
    config: row.config,
    enabled: row.enabled,
    run_order: row.run_order,
  }
  // Populate dynamic fields from existing config
  if (row.rule_type === 'keyword_blacklist') {
    configKeywords.value = row.config?.keywords || []
  } else if (row.rule_type === 'heat_threshold') {
    configMinHeat.value = row.config?.min_heat ?? 100
    configMaxHeat.value = row.config?.max_heat ?? 1000000
  } else if (row.rule_type === 'source_weight') {
    configWeights.value = row.config?.weights || { weibo: 1.0, baidu: 0.8, zhihu: 1.2 }
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  submitLoading.value = true
  try {
    const payload = {
      name: form.value.name,
      rule_type: form.value.rule_type as FilterRule['rule_type'],
      config: buildConfig(),
      enabled: form.value.enabled,
      run_order: form.value.run_order,
    }
    if (isEdit.value && editId.value) {
      await updateFilterRule(editId.value, payload)
      ElMessage.success('规则已更新')
    } else {
      await createFilterRule(payload)
      ElMessage.success('规则已创建')
    }
    dialogVisible.value = false
    await fetchRules()
  } finally {
    submitLoading.value = false
  }
}

async function handleToggleEnabled(row: FilterRule) {
  await updateFilterRule(row.id, {
    name: row.name,
    rule_type: row.rule_type,
    config: row.config,
    enabled: row.enabled,
    run_order: row.run_order,
  })
  ElMessage.success(row.enabled ? '已启用' : '已禁用')
}

async function handleDelete(row: FilterRule) {
  await deleteFilterRule(row.id)
  ElMessage.success('规则已删除')
  await fetchRules()
}

async function handleTriggerAll() {
  triggerLoading.value = true
  try {
    const res = await triggerFilterAll()
    ElMessage.success(`过滤完成：共 ${res.data.total} 条，通过 ${res.data.filtered}，拒绝 ${res.data.rejected}`)
  } finally {
    triggerLoading.value = false
  }
}

async function fetchRules() {
  loading.value = true
  try {
    const res = await getFilterRules()
    rules.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(fetchRules)
</script>

<style scoped lang="scss">
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.weight-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
</style>

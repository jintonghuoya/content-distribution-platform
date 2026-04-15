<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header>
        <span style="font-weight: 600">平台账号配置</span>
      </template>

      <el-alert
        title="在此配置各平台的凭据信息（Cookie、API Key 等），配置后即可在分发时使用对应平台。"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <el-collapse v-model="activeNames">
        <el-collapse-item
          v-for="platform in platforms"
          :key="platform.name"
          :name="platform.name"
        >
          <template #title>
            <span class="platform-title">
              {{ platform.display_name }}
              <el-tag v-if="hasCredentials(platform)" type="success" size="small" style="margin-left: 8px">
                已配置
              </el-tag>
              <el-tag v-else type="info" size="small" style="margin-left: 8px">未配置</el-tag>
            </span>
          </template>

          <el-form :model="platform" label-width="100px" class="platform-form">
            <el-form-item label="Cookie">
              <el-input
                v-model="platform.cookie"
                type="textarea"
                :rows="3"
                placeholder="从浏览器复制 Cookie 字符串"
              />
            </el-form-item>
            <el-form-item label="API Key">
              <el-input
                v-model="platform.api_key"
                type="password"
                show-password
                placeholder="平台 API Key"
              />
            </el-form-item>
            <el-form-item label="App ID">
              <el-input v-model="platform.app_id" placeholder="应用 ID" />
            </el-form-item>
            <el-form-item label="App Secret">
              <el-input
                v-model="platform.app_secret"
                type="password"
                show-password
                placeholder="应用密钥"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="saving === platform.name"
                @click="handleSave(platform)"
              >
                保存配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getPlatformConfigs, updatePlatformConfig } from '@/api/settings'
import type { PlatformConfig } from '@/types'

const platforms = ref<PlatformConfig[]>([])
const activeNames = ref<string[]>([])
const saving = ref<string | null>(null)

function hasCredentials(p: PlatformConfig) {
  return !!(p.cookie || p.api_key || p.app_secret)
}

async function fetchPlatforms() {
  try {
    const res = await getPlatformConfigs()
    platforms.value = res.data
  } catch {
    // API not available yet, show defaults
    platforms.value = [
      { name: 'weibo', display_name: '微博', id: 0, created_at: '', updated_at: '' },
      { name: 'wechat', display_name: '微信公众号', id: 0, created_at: '', updated_at: '' },
      { name: 'toutiao', display_name: '今日头条', id: 0, created_at: '', updated_at: '' },
      { name: 'xiaohongshu', display_name: '小红书', id: 0, created_at: '', updated_at: '' },
      { name: 'bilibili', display_name: 'B站', id: 0, created_at: '', updated_at: '' },
      { name: 'douyin', display_name: '抖音', id: 0, created_at: '', updated_at: '' },
    ]
  }
}

async function handleSave(platform: PlatformConfig) {
  saving.value = platform.name
  try {
    await updatePlatformConfig(platform.name, {
      display_name: platform.display_name,
      api_key: platform.api_key || '',
      cookie: platform.cookie || '',
      app_secret: platform.app_secret || '',
      app_id: platform.app_id || '',
    })
    ElMessage.success(`${platform.display_name} 配置已保存`)
  } finally {
    saving.value = null
  }
}

onMounted(fetchPlatforms)
</script>

<style scoped lang="scss">
.platform-title {
  font-size: 15px;
  font-weight: 500;
}

.platform-form {
  max-width: 700px;
  padding: 12px 0;
}
</style>

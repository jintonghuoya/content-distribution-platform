<template>
  <el-header class="app-header">
    <div class="header-left">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item v-if="$route.meta.title">
          {{ $route.meta.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-right">
      <el-tag :type="healthStatus === 'ok' ? 'success' : 'danger'" size="small" effect="dark">
        {{ healthStatus === 'ok' ? 'API 正常' : 'API 异常' }}
      </el-tag>
    </div>
  </el-header>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { checkHealth } from '@/api/health'

const healthStatus = ref<'ok' | 'error'>('ok')
let timer: ReturnType<typeof setInterval> | null = null

async function checkApiHealth() {
  try {
    const res = await checkHealth()
    healthStatus.value = res.data?.status === 'ok' ? 'ok' : 'error'
  } catch {
    healthStatus.value = 'error'
  }
}

onMounted(() => {
  checkApiHealth()
  timer = setInterval(checkApiHealth, 30000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped lang="scss">
.app-header {
  height: var(--cdp-header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
}
</style>

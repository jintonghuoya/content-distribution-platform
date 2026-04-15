<template>
  <el-aside :width="sidebarWidth" class="sidebar">
    <div class="sidebar-logo">
      <el-icon :size="24"><DataAnalysis /></el-icon>
      <span class="logo-text">CDP 管理后台</span>
    </div>
    <el-menu
      :default-active="activeRoute"
      :collapse="isCollapsed"
      router
      class="sidebar-menu"
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409eff"
    >
      <el-menu-item index="/">
        <el-icon><Odometer /></el-icon>
        <template #title>控制面板</template>
      </el-menu-item>
      <el-menu-item index="/sources">
        <el-icon><Connection /></el-icon>
        <template #title>数据源</template>
      </el-menu-item>
      <el-menu-item index="/topics">
        <el-icon><Document /></el-icon>
        <template #title>话题管理</template>
      </el-menu-item>
      <el-menu-item index="/filters">
        <el-icon><Filter /></el-icon>
        <template #title>过滤规则</template>
      </el-menu-item>
      <el-menu-item index="/content">
        <el-icon><EditPen /></el-icon>
        <template #title>内容管理</template>
      </el-menu-item>
      <el-menu-item index="/distribution">
        <el-icon><Promotion /></el-icon>
        <template #title>分发记录</template>
      </el-menu-item>
      <el-menu-item index="/revenue">
        <el-icon><Money /></el-icon>
        <template #title>收益统计</template>
      </el-menu-item>
      <el-menu-item index="/settings">
        <el-icon><Setting /></el-icon>
        <template #title>平台配置</template>
      </el-menu-item>
    </el-menu>
  </el-aside>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isCollapsed = ref(false)
const sidebarWidth = computed(() => isCollapsed.value ? '64px' : '220px')
const activeRoute = computed(() => route.path)
</script>

<style scoped lang="scss">
.sidebar {
  height: 100vh;
  background-color: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.sidebar-logo {
  height: var(--cdp-header-height);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-menu {
  border-right: none;
  height: calc(100vh - var(--cdp-header-height));
}
</style>

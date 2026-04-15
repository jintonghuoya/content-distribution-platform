import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { title: '控制面板' },
    },
    {
      path: '/sources',
      name: 'Sources',
      component: () => import('@/views/Sources.vue'),
      meta: { title: '数据源' },
    },
    {
      path: '/topics',
      name: 'Topics',
      component: () => import('@/views/Topics.vue'),
      meta: { title: '话题管理' },
    },
    {
      path: '/filters',
      name: 'Filters',
      component: () => import('@/views/Filters.vue'),
      meta: { title: '过滤规则' },
    },
    {
      path: '/content',
      name: 'Content',
      component: () => import('@/views/Content.vue'),
      meta: { title: '内容管理' },
    },
    {
      path: '/distribution',
      name: 'Distribution',
      component: () => import('@/views/Distribution.vue'),
      meta: { title: '分发记录' },
    },
    {
      path: '/revenue',
      name: 'Revenue',
      component: () => import('@/views/Revenue.vue'),
      meta: { title: '收益统计' },
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('@/views/Settings.vue'),
      meta: { title: '平台配置' },
    },
  ],
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || 'CDP'} - CDP 管理后台`
})

export default router

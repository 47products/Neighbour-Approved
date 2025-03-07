import { createRouter, createWebHistory } from 'vue-router'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import Dashboard from '@/views/Dashboard.vue'
import SystemHealth from '@/views/SystemHealth.vue'
import NotFound from '@/views/NotFound.vue'

const routes = [
  {
    path: '/',
    component: DashboardLayout,
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: 'Dashboard' }
      },
      {
        path: '/system/health',
        name: 'SystemHealth',
        component: SystemHealth,
        meta: { title: 'System Health' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: { title: '404 Not Found' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Update document title based on route meta
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title} | ${import.meta.env.VITE_APP_TITLE}`
  next()
})

export default router
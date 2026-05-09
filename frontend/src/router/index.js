import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/ChatView.vue')
  },
  {
    path: '/test',
    name: 'test',
    component: () => import('../testviews/TestLayout.vue')
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router

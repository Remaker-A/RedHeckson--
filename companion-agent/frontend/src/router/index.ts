import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/tent',
    },
    {
      path: '/soul',
      name: 'SoulCreation',
      component: () => import('../pages/SoulCreation.vue'),
    },
    {
      path: '/tent',
      name: 'TentRoom',
      component: () => import('../pages/TentRoom.vue'),
    },
    {
      path: '/settings',
      name: 'PersonalitySettings',
      component: () => import('../pages/PersonalitySettings.vue'),
    },
    {
      path: '/desktop',
      name: 'Desktop',
      component: () => import('../pages/Desktop.vue'),
    },
    {
      path: '/debug',
      name: 'DebugConsole',
      component: () => import('../pages/DebugConsole.vue'),
    },
  ],
})

export default router

import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/home',
    },
    {
      path: '/soul',
      name: 'SoulCreation',
      component: () => import('../pages/SoulCreation.vue'),
    },
    {
      path: '/home',
      name: 'Home',
      component: () => import('../pages/HomePage.vue'),
      meta: { tab: true },
    },
    {
      path: '/notes',
      name: 'Notes',
      component: () => import('../pages/NotesPage.vue'),
      meta: { tab: true },
    },
    {
      path: '/activity',
      name: 'Activity',
      component: () => import('../pages/ActivityPage.vue'),
      meta: { tab: true },
    },
    {
      path: '/me',
      name: 'Me',
      component: () => import('../pages/MePage.vue'),
      meta: { tab: true },
    },
    {
      path: '/home',
      name: 'Home',
      component: () => import('../pages/HomePage.vue'),
      meta: { tab: true },
    },
    {
      path: '/notes',
      name: 'Notes',
      component: () => import('../pages/NotesPage.vue'),
      meta: { tab: true },
    },
    {
      path: '/activity',
      name: 'Footprint',
      component: () => import('../pages/Footprint.vue'),
      meta: { tab: true },
    },
    {
      path: '/me',
      name: 'Me',
      component: () => import('../pages/MePage.vue'),
      meta: { tab: true },
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

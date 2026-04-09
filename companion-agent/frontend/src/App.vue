<script setup lang="ts">
import { computed, watchEffect } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import TabBar from './components/TabBar.vue'
import { useCompanionStore } from './stores/companion'

const route = useRoute()
const store = useCompanionStore()
const showTabBar = computed(() => !!route.meta.tab)

// Sync body class with theme
watchEffect(() => {
  if (store.isNight) {
    document.body.classList.add('night')
  } else {
    document.body.classList.remove('night')
  }
})
</script>

<template>
  <div class="app-shell" :class="{ night: store.isNight }">
    <RouterView v-slot="{ Component, route: r }">
      <Transition :name="(r.meta.transition as string) || 'fade'" mode="out-in">
        <component :is="Component" :key="r.path" />
      </Transition>
    </RouterView>
    <TabBar v-if="showTabBar" />
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
}
</style>

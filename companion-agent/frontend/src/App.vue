<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import TabBar from './components/TabBar.vue'

const route = useRoute()
const showTabBar = computed(() => !!route.meta.tab)
</script>

<template>
  <div class="app-shell">
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

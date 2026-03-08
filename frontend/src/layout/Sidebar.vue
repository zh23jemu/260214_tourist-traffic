<template>
  <el-menu
    :default-active="route.path"
    class="sidebar-menu"
    background-color="#001529"
    text-color="#a6adb4"
    active-text-color="#fff"
    router
  >
    <template v-for="item in menuRoutes" :key="item.path">
      <template v-if="item.children">
        <el-menu-item v-for="child in item.children" :key="child.path" :index="(item.path === '/' ? '' : item.path) + '/' + child.path">
          <el-icon v-if="child.meta?.icon">
            <component :is="child.meta.icon" />
          </el-icon>
          <span>{{ child.meta?.title }}</span>
        </el-menu-item>
      </template>
    </template>
  </el-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { routes } from '@/router'

const route = useRoute()

const menuRoutes = computed(() => {
  return routes.filter(item => !item.meta?.hidden && item.path === '/')
})
</script>

<style scoped>
.sidebar-menu {
  border-right: none;
}
.el-menu-item.is-active {
  background-color: var(--el-color-primary) !important;
}
</style>

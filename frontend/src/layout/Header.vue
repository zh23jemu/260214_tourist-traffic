<template>
  <div class="header-container">
    <div class="left-section">
      <span class="system-title">基于多源数据的荔波县旅游客流量影响因素分析与预测系统</span>
    </div>
    <div class="right-section">
      <el-dropdown @command="handleCommand">
        <span class="el-dropdown-link user-avatar">
          <el-avatar size="small" icon="UserFilled" />
          管理员
          <el-icon class="el-icon--right"><arrow-down /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { useUserStore } from '@/store/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 20px;
}
.system-title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}
.user-avatar {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #333;
  gap: 8px;
}
</style>

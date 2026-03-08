<template>
  <el-container class="layout-container">
    <el-aside width="220px">
      <div class="logo-box">
        <h3>旅游分析与预测系统</h3>
      </div>
      <Sidebar />
    </el-aside>
    <el-container>
      <el-header height="60px">
        <Header />
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
</script>

<style scoped>
.layout-container {
  height: 100vh;
}
.el-aside {
  background-color: #001529;
  color: #fff;
  transition: width 0.3s;
}
.logo-box {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border-bottom: 1px solid #002140;
}
.logo-box h3 {
  margin: 0;
  font-size: 16px;
  white-space: nowrap;
}
.el-header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  padding: 0;
}
.el-main {
  background-color: #f0f2f5;
  padding: 24px;
}
</style>

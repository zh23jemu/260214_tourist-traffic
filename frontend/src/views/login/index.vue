<template>
  <div class="login-container">
    <div class="login-bg"></div>
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>基于多源数据的荔波县旅游客流量影响因素分析与预测系统</span>
        </div>
      </template>
      <el-form :model="loginForm" :rules="rules" ref="loginFormRef" label-width="0">
        <el-form-item prop="username">
          <el-input v-model="loginForm.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="密码" prefix-icon="Lock" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" style="width: 100%;">
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { login } from '@/api'
import { ElMessage } from 'element-plus'

const loginFormRef = ref(null)
const loginForm = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}
const loading = ref(false)
const router = useRouter()
const userStore = useUserStore()

const handleLogin = () => {
  loginFormRef.value.validate(async valid => {
    if (valid) {
      loading.value = true
      try {
        const res = await login(loginForm)
        if (res && res.access_token) {
          userStore.setToken(res.access_token)
          ElMessage.success('登录成功')
          router.push('/')
        } else {
          ElMessage.error('登录失败: 未获取到 Token')
        }
      } catch (e) {
        console.error(e)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.login-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('/login_bg.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  z-index: 0;
}

.login-bg::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.3); /* Lighter transparent overlay */
  z-index: 1;
}

.box-card {
  width: 750px;
  z-index: 10;
  background-color: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  box-shadow: 0 8px 32px 0 rgba(100, 100, 111, 0.2);
}

.card-header {
  font-weight: bold;
  text-align: center;
  font-size: 24px;
  color: #1f2f3d;
  letter-spacing: 2px;
  white-space: nowrap;
}

:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.7) !important;
  height: 44px;
  font-size: 16px;
}

:deep(.el-button) {
  border-radius: 8px;
  font-size: 18px;
  letter-spacing: 4px;
  height: 48px;
  margin-top: 10px;
}
</style>

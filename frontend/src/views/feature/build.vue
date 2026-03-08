<template>
  <div class="feature-build">
    <el-card shadow="hover" header="构建特征工程">
      <el-form :model="form" label-width="120px" class="form-container">
        <el-form-item label="区县">
          <el-input v-model="form.county" placeholder="例如：荔波县" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" placeholder="构建开始日期" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" placeholder="构建结束日期" />
        </el-form-item>
        <el-form-item label="特征版本号">
          <el-input v-model="form.feature_version" placeholder="例如：v1" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleBuild" :loading="loading">
            开始构建特征
          </el-button>
        </el-form-item>
      </el-form>

      <div v-if="buildResult" class="result-box mt-20">
        <el-alert title="构建成功" type="success" :closable="false" show-icon>
          <p>特征版本：{{ buildResult.feature_version }}</p>
          <p>区县：{{ buildResult.county }}</p>
          <p>生成行数：{{ buildResult.rows_generated }} 行</p>
        </el-alert>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { buildFeatures } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const buildResult = ref(null)
const form = reactive({
  start_date: '2025-09-11',
  end_date: '2026-03-05',
  county: '荔波县',
  feature_version: 'v1'
})

const handleBuild = async () => {
  if (!form.county || !form.start_date || !form.end_date || !form.feature_version) {
    ElMessage.warning('请填写完整参数')
    return
  }
  loading.value = true
  try {
    const res = await buildFeatures(form)
    buildResult.value = res
    ElMessage.success('构建成功')
  } catch (e) {
    ElMessage.error('构建失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.form-container {
  max-width: 600px;
}
.mt-20 {
  margin-top: 20px;
}
.result-box p {
  margin: 5px 0;
}
</style>

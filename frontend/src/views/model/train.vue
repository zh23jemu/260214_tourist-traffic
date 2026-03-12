<template>
  <div class="model-train">
    <el-card shadow="hover" header="模型训练">
      <el-form :model="form" :inline="true" class="demo-form-inline">
        <el-form-item label="区县">
          <el-input v-model="form.county" placeholder="例如：荔波县" />
        </el-form-item>
        <el-form-item label="特征版本">
          <el-select v-model="form.feature_version" placeholder="选择特征版本" style="width: 180px">
            <el-option
              v-for="version in featureVersions"
              :key="version"
              :label="version"
              :value="version"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="预测天数(horizon)">
          <el-select v-model.number="form.horizon" placeholder="选择 horizon" style="width: 180px">
            <el-option label="7天" :value="7" />
            <el-option label="14天" :value="14" />
            <el-option label="30天" :value="30" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleTrain" :loading="training">触发训练</el-button>
        </el-form-item>
      </el-form>

      <div v-if="trainResult" class="result-box mt-20">
        <el-alert title="训练完成" type="success" :closable="false" show-icon>
          <p>模型版本：{{ trainResult.model_version }}</p>
          <p>算法：{{ trainResult.algorithm }}</p>
          <p>训练窗口：{{ trainResult.train_start }} ~ {{ trainResult.train_end }}</p>
          <p v-if="trainResult.metrics">
            MAE: {{ trainResult.metrics.mae }} | 
            RMSE: {{ trainResult.metrics.rmse }} | 
            MAPE: {{ trainResult.metrics.mape }}
          </p>
        </el-alert>
      </div>

      <el-divider>模型指标历史</el-divider>
      <el-button @click="loadMetrics" :loading="metricsLoading" class="mb-10">刷新指标列表</el-button>
      
      <el-table :data="metricsList" stripe style="width: 100%">
        <template #empty>
          <el-empty description="暂无模型指标" />
        </template>
        <el-table-column prop="model_version" label="模型版本" width="250" />
        <el-table-column prop="algorithm" label="算法" />
        <el-table-column prop="horizon" label="Horizon(天)" />
        <el-table-column prop="metrics.mae" label="MAE" />
        <el-table-column prop="metrics.rmse" label="RMSE" />
        <el-table-column prop="metrics.mape" label="MAPE" />
        <el-table-column label="训练窗口" width="200">
          <template #default="scope">
            {{ scope.row.train_start }} ~ {{ scope.row.train_end }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, watch } from 'vue'
import { trainModel, getModelMetrics, getFeatureVersions } from '@/api'
import { ElMessage } from 'element-plus'

const form = reactive({
  feature_version: '',
  horizon: 7,
  county: '荔波县'
})
const training = ref(false)
const trainResult = ref(null)
const featureVersions = ref([])

const metricsLoading = ref(false)
const metricsList = ref([])

const loadFeatureVersions = async () => {
  try {
    const res = await getFeatureVersions({ county: form.county || '荔波县' })
    featureVersions.value = Array.isArray(res?.versions) ? res.versions : []
    if (featureVersions.value.length > 0) {
      if (!featureVersions.value.includes(form.feature_version)) {
        form.feature_version = featureVersions.value[0]
      }
    } else {
      form.feature_version = ''
      ElMessage.warning('当前区县还没有可用的特征版本，请先到“特征构建”页面生成特征')
    }
  } catch (e) {
    console.error(e)
    featureVersions.value = []
  }
}

const handleTrain = async () => {
  if (!form.county || !form.feature_version || !form.horizon) {
    ElMessage.warning('请填写完整')
    return
  }
  training.value = true
  try {
    const res = await trainModel(form)
    trainResult.value = res
    ElMessage.success('训练成功')
    loadMetrics()
  } catch(e) {
    ElMessage.error('训练失败')
  } finally {
    training.value = false
  }
}

const loadMetrics = async () => {
  metricsLoading.value = true
  try {
    const res = await getModelMetrics({ county: form.county || '荔波县' })
    metricsList.value = Array.isArray(res) ? res : (res.data || [])
  } catch (e) {
    console.error(e)
  } finally {
    metricsLoading.value = false
  }
}

onMounted(() => {
  loadFeatureVersions()
  loadMetrics()
})

watch(() => form.county, async (value, oldValue) => {
  if (!value || value === oldValue) {
    return
  }
  await loadFeatureVersions()
  await loadMetrics()
})
</script>

<style scoped>
.mt-20 { margin-top: 20px; }
.mb-10 { margin-bottom: 10px; }
.result-box p { margin: 5px 0; }
</style>

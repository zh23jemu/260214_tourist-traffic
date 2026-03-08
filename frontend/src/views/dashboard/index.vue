<template>
  <div class="dashboard-container" v-loading="loading">
    <el-row class="mb-20">
      <el-col :span="24" style="text-align: right;">
        <el-button type="primary" icon="Download" @click="handleExport('csv')">导出 CSV 报表</el-button>
        <el-button type="success" icon="Picture" @click="handleExport('png')">导出 PNG 报表</el-button>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <span class="title">清洗数据行数</span>
            <span class="value">{{ data.clean_row_count || 0 }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <span class="title">特征数据行数</span>
            <span class="value">{{ data.feature_row_count || 0 }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <span class="title">预测数据行数</span>
            <span class="value">{{ data.prediction_row_count || 0 }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <span class="title">分析区县数</span>
            <span class="value">{{ data.county_count || 0 }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="12">
        <el-card header="最近实际客流趋势" shadow="hover">
          <e-charts :options="actualChartOpts" height="300px" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="最近预测客流趋势" shadow="hover">
          <e-charts :options="predictChartOpts" height="300px" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="24">
        <el-card header="最新模型指标" shadow="hover">
          <el-descriptions border :column="4" v-if="data.latest_model">
            <el-descriptions-item label="模型版本">{{ data.latest_model.model_version }}</el-descriptions-item>
            <el-descriptions-item label="算法">{{ data.latest_model.algorithm }}</el-descriptions-item>
            <el-descriptions-item label="MAE">{{ data.latest_model.metrics ? data.latest_model.metrics.mae : data.latest_model.mae }}</el-descriptions-item>
            <el-descriptions-item label="RMSE">{{ data.latest_model.metrics ? data.latest_model.metrics.rmse : data.latest_model.rmse }}</el-descriptions-item>
            <el-descriptions-item label="MAPE">{{ data.latest_model.metrics ? data.latest_model.metrics.mape : data.latest_model.mape }}</el-descriptions-item>
            <el-descriptions-item label="训练窗口">{{ data.latest_model.train_start }} ~ {{ data.latest_model.train_end }}</el-descriptions-item>
          </el-descriptions>
          <el-empty v-else description="暂无最新模型指标" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDashboardOverview } from '@/api'
import { downloadFile } from '@/utils/download'
import ECharts from '@/components/ECharts.vue'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const data = ref({})
const actualChartOpts = ref({})
const predictChartOpts = ref({})

const handleExport = (format) => {
  const url = `http://127.0.0.1:8000/api/v1/export/report?format=${format}`
  downloadFile(url, `report.${format}`)
}

const initActualChart = (actualList = []) => {
  const dates = actualList.map(item => item.date)
  const values = actualList.map(item => item.actual_count || item.value || item.count || 0)
  
  actualChartOpts.value = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', name: '客流量' },
    series: [{
      name: '实际客流量',
      data: values,
      type: 'line',
      smooth: true,
      color: '#409EFF',
      areaStyle: { opacity: 0.1 }
    }]
  }
}

const initPredictChart = (predictList = []) => {
  const dates = predictList.map(item => item.date)
  const values = predictList.map(item => item.y_pred || item.value || 0)
  
  predictChartOpts.value = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', name: '预测客流量' },
    series: [{
      name: '预测客流量',
      data: values,
      type: 'line',
      smooth: true,
      color: '#67C23A',
      areaStyle: { opacity: 0.1 }
    }]
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getDashboardOverview({ county: '荔波县' })
    data.value = res || {}
    initActualChart(data.value.recent_actual_series || data.value.recent_actual || [])
    initPredictChart(data.value.recent_prediction_series || data.value.recent_predict || [])
  } catch (e) {
    if(!data.value) data.value = {}
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.mt-20 {
  margin-top: 20px;
}
.stat-item {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 10px 0;
}
.stat-item .title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}
.stat-item .value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}
</style>

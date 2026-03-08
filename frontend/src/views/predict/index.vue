<template>
  <div class="predict-view">
    <el-card shadow="hover" header="数据预测">
      <el-form :model="form" :inline="true">
        <el-form-item label="模型版本">
          <el-select v-model="form.model_version" placeholder="请选择或输入模型版本" style="width: 250px;" v-loading="loadingModels" filterable allow-create>
            <el-option v-for="item in modelOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="预测天数">
          <el-select v-model.number="form.horizon" style="width: 100px;">
            <el-option label="7天" :value="7" />
            <el-option label="30天" :value="30" />
          </el-select>
        </el-form-item>
        <el-form-item label="起始日期">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width: 140px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handlePredict" :loading="predicting">生成预测</el-button>
          <el-button @click="loadPredictions" :loading="loadingData">查询结果</el-button>
        </el-form-item>
      </el-form>

      <div v-if="predictRes" class="mt-10 mb-20">
        <el-tag type="success">
          已成功写入 {{ predictRes.inserted_rows }} 行预测记录，开始日期 {{ predictRes.start_date }}
        </el-tag>
      </div>

      <el-divider>预测结果展示</el-divider>

      <div class="chart-container" style="margin-bottom: 30px;" v-if="predictionData.length">
        <e-charts :options="chartOpts" height="400px" />
      </div>

      <el-table :data="predictionData" stripe style="width: 100%" v-loading="loadingData">
        <template #empty>
          <el-empty description="暂无结果，请先生成预测或查询" />
        </template>
        <el-table-column prop="date" label="日期" />
        <el-table-column prop="county" label="区县" />
        <el-table-column prop="y_pred" label="预测值 (y_pred)">
          <template #default="{row}">{{ row.y_pred?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="y_low" label="下界 (y_low)">
          <template #default="{row}">{{ row.y_low?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="y_high" label="上界 (y_high)">
          <template #default="{row}">{{ row.y_high?.toFixed(2) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { predict, getPredictions, getModelMetrics } from '@/api'
import ECharts from '@/components/ECharts.vue'
import { ElMessage } from 'element-plus'

const form = reactive({
  model_version: '',
  horizon: 7,
  start_date: '2026-03-06'
})

const predicting = ref(false)
const predictRes = ref(null)

const loadingData = ref(false)
const predictionData = ref([])
const chartOpts = ref({})

const loadingModels = ref(false)
const modelOptions = ref([])

const loadModels = async () => {
  loadingModels.value = true
  try {
    const res = await getModelMetrics({ county: '荔波县' })
    const list = Array.isArray(res) ? res : (res.data || [])
    modelOptions.value = list.map(item => item.model_version)
  } catch (e) {
    ElMessage.error('获取模型列表失败')
  } finally {
    loadingModels.value = false
  }
}

onMounted(() => {
  loadModels()
})

const handlePredict = async () => {
  if (!form.model_version || !form.start_date) {
    ElMessage.warning('请输入模型版本和起始日期')
    return
  }
  predicting.value = true
  try {
    const res = await predict(form)
    predictRes.value = res
    ElMessage.success('预测生成完毕')
    loadPredictions()
  } catch (e) {
    ElMessage.error('生成预测失败')
  } finally {
    predicting.value = false
  }
}

const loadPredictions = async () => {
  if (!form.model_version) {
    ElMessage.warning('请输入要查询的模型版本')
    return
  }
  loadingData.value = true
  try {
    const res = await getPredictions({ model_version: form.model_version })
    predictionData.value = Array.isArray(res) ? res : (res.data || [])
    renderChart(predictionData.value)
  } catch (e) {
    ElMessage.error('查询预测记录失败')
  } finally {
    loadingData.value = false
  }
}

const renderChart = (data) => {
  if(!data.length) return
  const dates = data.map(item => item.date)
  const yPred = data.map(item => item.y_pred)
  const yLow = data.map(item => item.y_low)
  const yHigh = data.map(item => item.y_high)

  chartOpts.value = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['预测值', '预测上界', '预测下界'] },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: { type: 'value', name: '客流量' },
    series: [
      {
        name: '预测值',
        type: 'line',
        data: yPred,
        itemStyle: { color: '#409EFF' },
        smooth: true
      },
      {
        name: '预测上界',
        type: 'line',
        data: yHigh,
        lineStyle: { type: 'dashed', opacity: 0.5 },
        itemStyle: { color: '#F56C6C' },
        smooth: true
      },
      {
        name: '预测下界',
        type: 'line',
        data: yLow,
        lineStyle: { type: 'dashed', opacity: 0.5 },
        itemStyle: { color: '#E6A23C' },
        smooth: true
      }
    ]
  }
}
</script>

<style scoped>
.mt-10 { margin-top: 10px; }
.mb-20 { margin-bottom: 20px; }
</style>

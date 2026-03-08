<template>
  <div class="analysis-view">
    <el-card shadow="hover" header="影响因素相关性分析">
      <el-form inline>
        <el-form-item label="分析区县">
          <el-input v-model="county" placeholder="例如：荔波县" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData" :loading="loading">分析</el-button>
        </el-form-item>
      </el-form>

      <div class="chart-container mt-20" v-if="chartData.length" v-loading="loading">
        <e-charts :options="chartOpts" height="400px" />
      </div>

      <el-table :data="tableData" stripe style="width: 100%" class="mt-20" v-loading="loading">
        <template #empty>
          <el-empty description="暂无相关性数据" />
        </template>
        <el-table-column prop="factor" label="特征/因素名称" />
        <el-table-column prop="correlation" label="Pearson 相关系数">
          <template #default="{row}">
            <el-tag :type="getCorrType(row.correlation)">
              {{ row.correlation?.toFixed(4) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getCorrelation } from '@/api'
import ECharts from '@/components/ECharts.vue'
import { ElMessage } from 'element-plus'

const county = ref('荔波县')
const loading = ref(false)
const chartData = ref([])
const tableData = ref([])
const chartOpts = ref({})

const getCorrType = (val) => {
  const num = Math.abs(val || 0)
  if (num > 0.7) return 'danger'
  if (num > 0.4) return 'warning'
  return 'info'
}

const fetchData = async () => {
  if (!county.value) return
  loading.value = true
  try {
    const res = await getCorrelation({ county: county.value })
    // Assume res is [ { feature: "x", correlation: 0.8 } ]
    let parsedData = []
    if (Array.isArray(res)) {
      parsedData = res.map(item => ({
        factor: item.feature || item.factor || item.name,
        correlation: item.correlation || item.value || 0
      }))
    } else if (typeof res === 'object' && res.data && Array.isArray(res.data)) {
      parsedData = res.data.map(item => ({
        factor: item.feature || item.factor || item.name,
        correlation: item.correlation || item.value || 0
      }))
    } else if (typeof res === 'object') {
      parsedData = Object.keys(res).map(k => ({
        factor: k,
        correlation: res[k]
      }))
    }
    
    // sort by absolute value descending
    parsedData.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation))
    tableData.value = parsedData
    chartData.value = parsedData
    renderChart(parsedData)
  } catch (e) {
    ElMessage.error('查询相关性失败')
  } finally {
    loading.value = false
  }
}

const renderChart = (data) => {
  const factors = data.map(i => i.factor)
  const values = data.map(i => i.correlation)

  chartOpts.value = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: {
      type: 'category',
      data: factors,
      axisLabel: { interval: 0, rotate: 30 }
    },
    yAxis: { type: 'value', name: 'Pearson Correlation' },
    series: [
      {
        name: '相关系数',
        type: 'bar',
        data: values.map(val => ({
          value: val,
          itemStyle: { color: val > 0 ? '#409EFF' : '#F56C6C' }
        }))
      }
    ]
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.mt-20 { margin-top: 20px; }
</style>

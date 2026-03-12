<template>
  <div class="data-import">
    <el-card shadow="hover" header="数据导入与预览">
      <el-upload
        class="upload-demo"
        drag
        action="#"
        :http-request="customUpload"
        :show-file-list="false"
        accept=".xls,.xlsx"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处，或 <em>点击上传Excel</em>
        </div>
      </el-upload>

      <div v-if="importResult" class="result-box mt-20">
        <el-alert title="导入结果" type="success" :closable="false">
          <div>
            Batch ID: {{ importResult.batch_id }} <br/>
            总行数: {{ importResult.total_rows }} <br/>
            成功数: {{ importResult.success_rows }} <br/>
            失败数: {{ importResult.error_rows }}
          </div>
          <div v-if="importResult.errors && importResult.errors.length > 0" class="mt-10">
            <strong>错误列表:</strong>
            <ul>
              <li v-for="(err, idx) in importResult.errors" :key="idx">{{ err }}</li>
            </ul>
          </div>
        </el-alert>
      </div>

      <el-divider>数据预览查询</el-divider>
      
      <el-form :inline="true" :model="queryParams" class="demo-form-inline">
        <el-form-item label="开始日期">
          <el-date-picker v-model="queryParams.start_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="queryParams.end_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" />
        </el-form-item>
        <el-form-item label="区县">
          <el-input v-model="queryParams.county" placeholder="例如：荔波县" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handlePreview" :loading="previewLoading">查询预览</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="previewData" stripe style="width: 100%" class="mt-20">
        <template #empty>
          <el-empty description="暂无预览数据" />
        </template>
        <el-table-column prop="date" label="日期" width="180" />
        <el-table-column prop="county" label="区县" width="150" />
        <el-table-column prop="actual_count" label="实际客流量" />
        <el-table-column prop="quality_flag" label="质量标记">
          <template #default="scope">
            <el-tag :type="scope.row.quality_flag === 'ok' ? 'success' : 'warning'">
              {{ scope.row.quality_flag || '未知' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { importExcel, getPreviewData } from '@/api'
import { ElMessage } from 'element-plus'

const importResult = ref(null)
const previewData = ref([])
const previewLoading = ref(false)
const queryParams = reactive({
  start_date: '2025-09-11',
  end_date: '2026-03-05',
  county: '荔波县'
})

const customUpload = async (options) => {
  const formData = new FormData()
  formData.append('file', options.file)
  try {
    const res = await importExcel(formData)
    importResult.value = res
    ElMessage.success(`导入完成，成功 ${res.success_rows} 条`)
  } catch (e) {
    ElMessage.error('导入失败')
  }
}

const handlePreview = async () => {
  previewLoading.value = true
  try {
    const res = await getPreviewData(queryParams)
    previewData.value = Array.isArray(res) ? res : (res.data || [])
  } catch (e) {
    ElMessage.error('预览获取失败')
  } finally {
    previewLoading.value = false
  }
}
</script>

<style scoped>
.mt-20 {
  margin-top: 20px;
}
.mt-10 {
  margin-top: 10px;
}
.result-box ul {
  margin: 5px 0 0 20px;
  padding: 0;
}
</style>

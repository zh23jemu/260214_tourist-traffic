import request from '@/utils/request'

export const login = (data) => request.post('/api/v1/auth/login', data)

export const importExcel = (data) => request.post('/api/v1/data/import/excel', data, {
    headers: { 'Content-Type': 'multipart/form-data' }
})

export const getPreviewData = (params) => request.get('/api/v1/data/preview', { params })
export const getDataRange = (params) => request.get('/api/v1/data/range', { params })

export const buildFeatures = (data) => request.post('/api/v1/features/build', data)

export const trainModel = (data) => request.post('/api/v1/models/train', data)

export const getModelMetrics = (params) => request.get('/api/v1/models/metrics', { params })

export const predict = (data) => request.post('/api/v1/models/predict', data)

export const getPredictions = (params) => request.get('/api/v1/predictions', { params })

export const getCorrelation = (params) => request.get('/api/v1/analysis/correlation', { params })

export const getDashboardOverview = (params) => request.get('/api/v1/dashboard/overview', { params })

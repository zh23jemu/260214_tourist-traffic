import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'
import Layout from '@/layout/index.vue'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/login/index.vue'),
        meta: { hidden: true }
    },
    {
        path: '/',
        component: Layout,
        redirect: '/dashboard',
        children: [
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: () => import('@/views/dashboard/index.vue'),
                meta: { title: '看板概览', icon: 'Odometer' }
            },
            {
                path: 'data',
                name: 'DataImport',
                component: () => import('@/views/data/import.vue'),
                meta: { title: '数据导入', icon: 'UploadFilled' }
            },
            {
                path: 'feature',
                name: 'FeatureBuild',
                component: () => import('@/views/feature/build.vue'),
                meta: { title: '特征构建', icon: 'Operation' }
            },
            {
                path: 'model',
                name: 'ModelTrain',
                component: () => import('@/views/model/train.vue'),
                meta: { title: '模型训练', icon: 'Aim' }
            },
            {
                path: 'predict',
                name: 'Predict',
                component: () => import('@/views/predict/index.vue'),
                meta: { title: '数据预测', icon: 'TrendCharts' }
            },
            {
                path: 'analysis',
                name: 'Analysis',
                component: () => import('@/views/analysis/correlation.vue'),
                meta: { title: '相关性分析', icon: 'DataAnalysis' }
            }
        ]
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const userStore = useUserStore()
    if (to.path !== '/login' && !userStore.token) {
        next('/login')
    } else {
        next()
    }
})

export { routes }
export default router

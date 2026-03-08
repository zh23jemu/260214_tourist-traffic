import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import router from '@/router'

const service = axios.create({
    baseURL: 'http://127.0.0.1:8000',
    timeout: 30000
})

service.interceptors.request.use(
    config => {
        const userStore = useUserStore()
        if (userStore.token) {
            config.headers['Authorization'] = `Bearer ${userStore.token}`
        }
        return config
    },
    error => {
        return Promise.reject(error)
    }
)

service.interceptors.response.use(
    response => {
        return response.data
    },
    error => {
        if (error.response) {
            const { status } = error.response
            if (status === 401) {
                ElMessage.error('需要重新登录')
                const userStore = useUserStore()
                userStore.logout()
                router.push('/login')
            } else {
                ElMessage.error(error.response.data?.detail || '接口请求错误')
            }
        } else {
            ElMessage.error('网络异常，请稍后重试')
        }
        return Promise.reject(error)
    }
)

export default service

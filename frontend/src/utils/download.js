import request from './request'
import { ElMessage } from 'element-plus'

export function downloadFile(url, filename) {
    return request({
        url: url,
        method: 'get',
        responseType: 'blob'
    }).then(res => {
        const blob = new Blob([res])
        const link = document.createElement('a')
        link.href = window.URL.createObjectURL(blob)
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(link.href)
    }).catch(e => {
        console.error('下载文件失败', e)
        ElMessage.error('文件下载失败')
    })
}

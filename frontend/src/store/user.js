import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
    const token = ref(localStorage.getItem('token') || '')

    function setToken(value) {
        token.value = value
        localStorage.setItem('token', value)
    }

    function logout() {
        token.value = ''
        localStorage.removeItem('token')
    }

    return { token, setToken, logout }
})

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'

import App from './App.vue'
import BenchmarkViewer from './components/BenchmarkViewer.vue'

const routes = [
  { path: '/', component: BenchmarkViewer }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

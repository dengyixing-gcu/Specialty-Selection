<template>
  <div class="result-container">
    <el-container>
      <el-header class="result-header">
        <h1>选课结果</h1>
        <div class="header-right">
          <el-button type="primary" @click="$router.push('/courses')">
            返回选课页面
          </el-button>
          <el-button type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>

      <el-main>
        <div v-if="loading" class="loading-section">
          <el-skeleton :rows="5" animated />
        </div>

        <div v-else-if="result" class="result-content">
          <el-card class="result-card">
            <template #header>
              <div class="result-header-card">
                <el-icon :size="40" color="#67C23A"><CircleCheck /></el-icon>
                <h2>选课成功</h2>
              </div>
            </template>

            <el-descriptions :column="1" border>
              <el-descriptions-item label="课程名称">
                {{ result.courseName }}
              </el-descriptions-item>
              <el-descriptions-item label="选课时间">
                {{ formatTime(result.selectedAt) }}
              </el-descriptions-item>
              <el-descriptions-item label="选课方式">
                <el-tag :type="result.isAutoAllocated ? 'warning' : 'success'">
                  {{ result.isAutoAllocated ? '系统自动分配' : '自主选课' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>

            <div v-if="result.isAutoAllocated" class="auto-allocate-notice">
              <el-alert
                title="系统分配说明"
                type="info"
                description="由于您在选课期间未进行选课操作，系统已为您随机分配到当前课程。"
                show-icon
                :closable="false"
              />
            </div>
          </el-card>
        </div>

        <div v-else class="no-result">
          <el-result
            icon="warning"
            title="暂无选课结果"
            sub-title="您尚未选课或选课尚未开始"
          >
            <template #extra>
              <el-button type="primary" @click="$router.push('/courses')">
                前往选课
              </el-button>
            </template>
          </el-result>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { CircleCheck } from '@element-plus/icons-vue'
import api from '@/utils/api'

const router = useRouter()
const loading = ref(true)
const result = ref(null)

const loadResult = async () => {
  try {
    const response = await api.get('/api/selection/result')
    if (response.data.hasSelected) {
      result.value = response.data
    }
  } catch (error) {
    ElMessage.error('加载选课结果失败')
  } finally {
    loading.value = false
  }
}

const formatTime = (timeStr) => {
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  localStorage.removeItem('userRole')
  router.push('/login')
}

onMounted(() => {
  loadResult()
})
</script>

<style scoped>
.result-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.result-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
}

.result-header h1 {
  margin: 0;
  font-size: 24px;
}

.header-right {
  display: flex;
  gap: 10px;
}

.loading-section {
  max-width: 600px;
  margin: 50px auto;
  padding: 20px;
}

.result-content {
  max-width: 600px;
  margin: 50px auto;
}

.result-card {
  border-radius: 10px;
}

.result-header-card {
  display: flex;
  align-items: center;
  gap: 15px;
}

.result-header-card h2 {
  margin: 0;
  color: #67C23A;
}

.auto-allocate-notice {
  margin-top: 20px;
}

.no-result {
  max-width: 600px;
  margin: 50px auto;
}
</style>

<template>
  <div class="courses-container">
    <el-container>
      <el-header class="courses-header">
        <h1>学生选课系统</h1>
        <div class="header-right">
          <span class="welcome">欢迎，{{ user?.name || '同学' }}</span>
          <el-button type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>

      <el-main>
        <!-- Countdown Timer -->
        <div v-if="countdownText" class="countdown-section">
          <el-alert
            :title="countdownText"
            :type="countdownType"
            show-icon
            :closable="false"
          />
        </div>

        <!-- Course Selection Status -->
        <div v-if="selectionStatus?.hasSelected" class="selected-status">
          <el-result
            icon="success"
            title="您已成功选课"
            :sub-title="`已选课程：${selectionStatus.selection?.courseName}`"
          >
            <template #extra>
              <el-button type="primary" @click="$router.push('/result')">
                查看选课结果
              </el-button>
            </template>
          </el-result>
        </div>

        <!-- Course Cards -->
        <div v-else class="courses-grid">
          <el-card
            v-for="course in courses"
            :key="course.id"
            class="course-card"
            :class="{ 'course-full': course.enrolledCount >= course.capacity }"
          >
            <template #header>
              <div class="course-header">
                <span class="course-name">{{ course.name }}</span>
                <el-tag
                  :type="course.enrolledCount >= course.capacity ? 'danger' : 'success'"
                  effect="dark"
                >
                  {{ course.enrolledCount >= course.capacity ? '已满' : '可选' }}
                </el-tag>
              </div>
            </template>

            <div class="course-info">
              <div class="info-item">
                <span class="label">课程容量：</span>
                <span class="value">{{ course.capacity }} 人</span>
              </div>
              <div class="info-item">
                <span class="label">已选人数：</span>
                <span class="value">{{ course.enrolledCount }} 人</span>
              </div>
              <div class="info-item">
                <span class="label">剩余名额：</span>
                <span class="value" :class="{ 'text-danger': course.enrolledCount >= course.capacity }">
                  {{ course.capacity - course.enrolledCount }} 人
                </span>
              </div>

              <el-progress
                :percentage="Math.round((course.enrolledCount / course.capacity) * 100)"
                :color="getProgressColor(course)"
                :show-text="false"
                class="course-progress"
              />
            </div>

            <el-button
              type="primary"
              :disabled="course.enrolledCount >= course.capacity || !isOpen"
              :loading="selectingCourseId === course.id"
              class="select-button"
              @click="handleSelectCourse(course)"
            >
              {{ course.enrolledCount >= course.capacity ? '课程已满' : '选择此课程' }}
            </el-button>
          </el-card>
        </div>

        <!-- No courses message -->
        <el-empty v-if="courses.length === 0" description="暂无课程信息" />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()

const user = ref(null)
const courses = ref([])
const selectionStatus = ref(null)
const isOpen = ref(false)
const openTime = ref(null)
const durationMinutes = ref(30)
const selectingCourseId = ref(null)
const countdownText = ref('')
const countdownType = ref('info')

let countdownTimer = null

const loadUser = () => {
  const savedUser = localStorage.getItem('user')
  if (savedUser) {
    user.value = JSON.parse(savedUser)
  }
}

const loadCourses = async () => {
  try {
    const response = await api.get('/api/courses')
    courses.value = response.data
  } catch (error) {
    ElMessage.error('加载课程信息失败')
  }
}

const loadSelectionStatus = async () => {
  try {
    const response = await api.get('/api/selection/status')
    selectionStatus.value = response.data
    isOpen.value = response.data.isOpen
    openTime.value = response.data.openTime
    durationMinutes.value = response.data.durationMinutes
    updateCountdown()
  } catch (error) {
    console.error('Failed to load selection status', error)
  }
}

const updateCountdown = () => {
  if (!openTime.value) {
    countdownText.value = ''
    return
  }

  const now = new Date()
  const open = new Date(openTime.value)
  const close = new Date(open.getTime() + durationMinutes.value * 60 * 1000)

  if (now < open) {
    // Before opening
    const diff = open - now
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    const seconds = Math.floor((diff % (1000 * 60)) / 1000)
    countdownText.value = `距离选课开放还有 ${hours}小时${minutes}分${seconds}秒`
    countdownType.value = 'info'
  } else if (now < close) {
    // During selection
    const diff = close - now
    const minutes = Math.floor(diff / (1000 * 60))
    const seconds = Math.floor((diff % (1000 * 60)) / 1000)
    countdownText.value = `选课进行中，剩余时间 ${minutes}分${seconds}秒`
    countdownType.value = 'success'
    isOpen.value = true
  } else {
    // After closing
    countdownText.value = '选课已结束'
    countdownType.value = 'warning'
    isOpen.value = false
  }
}

const getProgressColor = (course) => {
  const percentage = (course.enrolledCount / course.capacity) * 100
  if (percentage >= 90) return '#F56C6C'
  if (percentage >= 70) return '#E6A23C'
  return '#67C23A'
}

const handleSelectCourse = async (course) => {
  try {
    await ElMessageBox.confirm(
      `确定要选择「${course.name}」吗？选定后不可更改！`,
      '确认选课',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    selectingCourseId.value = course.id

    const response = await api.post('/api/selection/select', {
      courseId: course.id
    })

    if (response.data.success) {
      ElMessage.success('选课成功！')
      await loadSelectionStatus()
    } else {
      ElMessage.error(response.data.message || '选课失败')
      await loadCourses()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '选课失败')
      await loadCourses()
    }
  } finally {
    selectingCourseId.value = null
  }
}

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  localStorage.removeItem('userRole')
  router.push('/login')
}

onMounted(() => {
  loadUser()
  loadCourses()
  loadSelectionStatus()

  // Update countdown every second
  countdownTimer = setInterval(() => {
    updateCountdown()
    // Refresh courses every 5 seconds
    if (Date.now() % 5000 < 1000) {
      loadCourses()
    }
  }, 1000)
})

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})
</script>

<style scoped>
.courses-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.courses-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
}

.courses-header h1 {
  margin: 0;
  font-size: 24px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.welcome {
  font-size: 14px;
}

.countdown-section {
  margin-bottom: 20px;
}

.selected-status {
  margin: 50px auto;
  max-width: 600px;
}

.courses-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  padding: 20px;
}

.course-card {
  border-radius: 10px;
  transition: transform 0.3s, box-shadow 0.3s;
}

.course-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.course-card.course-full {
  opacity: 0.7;
}

.course-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.course-name {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.course-info {
  margin-bottom: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 14px;
}

.label {
  color: #909399;
}

.value {
  color: #303133;
  font-weight: bold;
}

.text-danger {
  color: #F56C6C;
}

.course-progress {
  margin-top: 10px;
}

.select-button {
  width: 100%;
}
</style>

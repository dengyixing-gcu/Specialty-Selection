<template>
  <div class="admin-container">
    <el-container>
      <el-header class="admin-header">
        <h1>管理员控制台</h1>
        <div class="header-right">
          <span class="welcome">欢迎，管理员</span>
          <el-button type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>

      <el-main>
        <el-tabs v-model="activeTab" type="border-card">
          <!-- Student Import Tab -->
          <el-tab-pane label="学生导入" name="import">
            <el-card>
              <template #header>
                <span>批量导入学生信息</span>
              </template>

              <el-upload
                ref="uploadRef"
                class="upload-demo"
                drag
                :auto-upload="false"
                :limit="1"
                accept=".xlsx,.xls"
                :on-change="handleFileChange"
                :on-exceed="handleExceed"
              >
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  将 Excel 文件拖到此处，或<em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    只能上传 .xlsx/.xls 文件，文件应包含学号和姓名两列
                  </div>
                </template>
              </el-upload>

              <div class="upload-actions">
                <el-button type="primary" :loading="importing" @click="handleImport">
                  开始导入
                </el-button>
                <el-button @click="handleDownloadTemplate">
                  下载模板
                </el-button>
              </div>

              <div v-if="importResult" class="import-result">
                <el-alert
                  :title="`导入完成：成功 ${importResult.importedCount} 人，跳过 ${importResult.skippedCount} 人`"
                  :type="importResult.skippedCount > 0 ? 'warning' : 'success'"
                  show-icon
                  :closable="false"
                />
                <div v-if="importResult.passwords && importResult.passwords.length > 0" class="passwords-section">
                  <h4>学生密码列表：</h4>
                  <el-table :data="passwordTableData" border style="width: 100%">
                    <el-table-column prop="index" label="序号" width="80" />
                    <el-table-column prop="studentNo" label="学号" />
                    <el-table-column prop="password" label="密码" />
                  </el-table>
                </div>
              </div>
            </el-card>
          </el-tab-pane>

          <!-- Selection Time Setting Tab -->
          <el-tab-pane label="选课时间设置" name="time">
            <el-card>
              <template #header>
                <span>设置选课开放时间</span>
              </template>

              <el-form :model="timeForm" label-width="120px">
                <el-form-item label="开放时间">
                  <el-date-picker
                    v-model="timeForm.openTime"
                    type="datetime"
                    placeholder="选择开放时间"
                    format="YYYY-MM-DD HH:mm:ss"
                    value-format="YYYY-MM-DDTHH:mm:ss"
                    :disabled-date="disabledDate"
                  />
                </el-form-item>

                <el-form-item label="开放时长">
                  <el-input-number
                    v-model="timeForm.durationMinutes"
                    :min="1"
                    :max="120"
                    :step="5"
                  />
                  <span class="duration-hint">分钟</span>
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" :loading="savingTime" @click="handleSaveTime">
                    保存设置
                  </el-button>
                </el-form-item>
              </el-form>

              <div v-if="currentTimeConfig" class="current-config">
                <el-alert
                  :title="`当前设置：${formatTime(currentTimeConfig.openTime)} 开放，持续 ${currentTimeConfig.durationMinutes} 分钟`"
                  type="info"
                  show-icon
                  :closable="false"
                />
              </div>
            </el-card>
          </el-tab-pane>

          <!-- Course Status Tab -->
          <el-tab-pane label="选课状态" name="status">
            <el-card>
              <template #header>
                <span>课程选课状态</span>
              </template>

              <el-button type="primary" @click="loadCourseStatus" :loading="loadingStatus">
                刷新状态
              </el-button>

              <div v-if="courseStatus" class="course-status">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="课程总数">
                    {{ courseStatus.courses?.length || 0 }} 门
                  </el-descriptions-item>
                  <el-descriptions-item label="总容量">
                    {{ courseStatus.totalCapacity }} 人
                  </el-descriptions-item>
                  <el-descriptions-item label="已选人数">
                    {{ courseStatus.totalEnrolled }} 人
                  </el-descriptions-item>
                  <el-descriptions-item label="剩余名额">
                    {{ courseStatus.totalRemaining }} 人
                  </el-descriptions-item>
                </el-descriptions>

                <el-table :data="courseStatus.courses" border style="width: 100%; margin-top: 20px;">
                  <el-table-column prop="name" label="课程名称" />
                  <el-table-column prop="capacity" label="容量" width="100" />
                  <el-table-column prop="enrolledCount" label="已选" width="100" />
                  <el-table-column label="剩余" width="100">
                    <template #default="{ row }">
                      {{ row.capacity - row.enrolledCount }}
                    </template>
                  </el-table-column>
                  <el-table-column label="状态" width="100">
                    <template #default="{ row }">
                      <el-tag :type="row.enrolledCount >= row.capacity ? 'danger' : 'success'">
                        {{ row.enrolledCount >= row.capacity ? '已满' : '可选' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-card>
          </el-tab-pane>
        </el-tabs>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '@/utils/api'

const router = useRouter()
const activeTab = ref('import')
const uploadRef = ref(null)
const importing = ref(false)
const importResult = ref(null)
const selectedFile = ref(null)

const timeForm = reactive({
  openTime: '',
  durationMinutes: 30
})
const savingTime = ref(false)
const currentTimeConfig = ref(null)

const courseStatus = ref(null)
const loadingStatus = ref(false)

const passwordTableData = computed(() => {
  if (!importResult.value?.passwords) return []
  return importResult.value.passwords.map((password, index) => ({
    index: index + 1,
    studentNo: `学生${index + 1}`,
    password
  }))
})

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const handleImport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  importing.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const response = await api.post('/api/admin/import-students', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    importResult.value = response.data
    ElMessage.success('导入完成')
    uploadRef.value?.clearFiles()
    selectedFile.value = null
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '导入失败')
  } finally {
    importing.value = false
  }
}

const handleDownloadTemplate = () => {
  // Create a simple Excel template
  const template = '学号,姓名\n2024001,张三\n2024002,李四'
  const blob = new Blob([template], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'student_template.csv'
  a.click()
  URL.revokeObjectURL(url)
}

const disabledDate = (time) => {
  return time.getTime() < Date.now() - 8.64e7 // Can't select past dates
}

const handleSaveTime = async () => {
  if (!timeForm.openTime) {
    ElMessage.warning('请选择开放时间')
    return
  }

  savingTime.value = true
  try {
    await api.post('/api/admin/config', {
      openTime: timeForm.openTime,
      durationMinutes: timeForm.durationMinutes
    })

    currentTimeConfig.value = {
      openTime: timeForm.openTime,
      durationMinutes: timeForm.durationMinutes
    }

    ElMessage.success('选课时间设置成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '设置失败')
  } finally {
    savingTime.value = false
  }
}

const loadCourseStatus = async () => {
  loadingStatus.value = true
  try {
    const response = await api.get('/api/courses/status')
    courseStatus.value = response.data
  } catch (error) {
    ElMessage.error('加载选课状态失败')
  } finally {
    loadingStatus.value = false
  }
}

const formatTime = (timeStr) => {
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  localStorage.removeItem('userRole')
  router.push('/login')
}

onMounted(() => {
  loadCourseStatus()
})
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.admin-header {
  background: linear-gradient(135deg, #409EFF 0%, #337ab7 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
}

.admin-header h1 {
  margin: 0;
  font-size: 24px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.upload-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.import-result {
  margin-top: 20px;
}

.passwords-section {
  margin-top: 20px;
}

.passwords-section h4 {
  margin-bottom: 10px;
  color: #303133;
}

.duration-hint {
  margin-left: 10px;
  color: #909399;
}

.current-config {
  margin-top: 20px;
}

.course-status {
  margin-top: 20px;
}
</style>

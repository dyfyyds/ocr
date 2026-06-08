<template>
  <el-container style="min-height: 100vh">
    <el-aside width="200px" style="background: #001529">
      <div style="color: #fff; text-align: center; padding: 20px; font-size: 16px; font-weight: bold">项目管理系统</div>
      <el-menu :default-active="'/ocr'" background-color="#001529" text-color="#ffffffb3" active-text-color="#409eff" router>
        <el-menu-item index="/dashboard"><el-icon><House /></el-icon><span>工作台</span></el-menu-item>
        <el-menu-item v-if="hasRole(['admin', 'business'])" index="/register"><el-icon><DocumentAdd /></el-icon><span>立项登记</span></el-menu-item>
        <el-menu-item v-if="hasRole(['admin', 'business'])" index="/projects"><el-icon><Folder /></el-icon><span>项目档案</span></el-menu-item>
        <el-menu-item index="/ocr"><el-icon><Search /></el-icon><span>OCR 识别</span></el-menu-item>
        <el-menu-item v-if="hasRole(['admin'])" index="/audit"><el-icon><Checked /></el-icon><span>立项审核</span></el-menu-item>
        <el-menu-item v-if="hasRole(['admin'])" index="/users"><el-icon><User /></el-icon><span>用户管理</span></el-menu-item>
        <el-menu-item v-if="hasRole(['admin'])" index="/dict"><el-icon><Collection /></el-icon><span>数据字典</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e8e8e8">
        <span style="font-size: 18px; font-weight: 500">OCR 识别</span>
        <div>
          <span style="margin-right: 16px">{{ userStore.userInfo?.real_name || userStore.userInfo?.username }}</span>
          <el-button type="danger" text @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main>
        <!-- 文件上传区域 -->
        <el-card shadow="never" style="margin-bottom: 16px">
          <template #header><span style="font-weight: 600">选择文件进行 OCR 识别</span></template>
          <input ref="fileInputRef" type="file" accept=".docx,.pdf,.jpg,.jpeg,.png,.bmp,.tiff" style="display:none" @change="onFileSelected" />
          <div class="upload-area">
            <el-icon style="font-size: 48px; color: #409eff"><Document /></el-icon>
            <p style="margin: 12px 0 4px; font-size: 15px">选择 Word / PDF / 图片文件</p>
            <p style="color: #999; font-size: 13px; margin: 0 0 20px">支持 .docx / .pdf / .jpg / .png，最大 20MB</p>
            <el-button type="primary" size="large" :loading="recognizing" @click="fileInputRef.click()">
              <el-icon style="margin-right: 6px"><Search /></el-icon>
              选择文件并识别
            </el-button>
          </div>
        </el-card>

        <!-- 识别结果 -->
        <el-card v-if="ocrResult" shadow="never" style="margin-bottom: 16px">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600">识别结果</span>
              <div>
                <el-tag :type="ocrResult.source === 'paddleocr' ? 'warning' : 'success'" size="small" style="margin-right: 8px">
                  {{ ocrResult.source === 'paddleocr' ? 'PaddleOCR' : 'python-docx' }}
                </el-tag>
                <el-tag size="small">{{ ocrResult.file_name }}</el-tag>
              </div>
            </div>
          </template>

          <!-- 提取的结构化字段 -->
          <el-descriptions :column="2" border style="margin-bottom: 16px">
            <el-descriptions-item label="项目名称">
              <span :class="{ 'highlight-empty': !ocrResult.extracted?.project_name }">
                {{ ocrResult.extracted?.project_name || '未识别到' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="合同编号">
              <span :class="{ 'highlight-empty': !ocrResult.extracted?.contract_no }">
                {{ ocrResult.extracted?.contract_no || '未识别到' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="合同金额">
              <span :class="{ 'highlight-empty': !ocrResult.extracted?.contract_amount }">
                {{ ocrResult.extracted?.contract_amount ? '¥' + Number(ocrResult.extracted.contract_amount).toLocaleString() : '未识别到' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="签订日期">
              <span :class="{ 'highlight-empty': !ocrResult.extracted?.sign_date }">
                {{ ocrResult.extracted?.sign_date || '未识别到' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="客户名称">
              <span :class="{ 'highlight-empty': !ocrResult.extracted?.customer_name }">
                {{ ocrResult.extracted?.customer_name || '未识别到' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="发票号码">
              <span :class="{ 'highlight-empty': !ocrResult.extracted?.invoice_no }">
                {{ ocrResult.extracted?.invoice_no || '未识别到' }}
              </span>
            </el-descriptions-item>
          </el-descriptions>

          <!-- 操作按钮 -->
          <div style="margin-bottom: 16px; display: flex; gap: 12px">
            <el-button type="success" @click="goToRegister">
              <el-icon style="margin-right: 4px"><DocumentAdd /></el-icon>
              用此结果创建项目
            </el-button>
            <el-button @click="resetAll">
              <el-icon style="margin-right: 4px"><RefreshRight /></el-icon>
              重新识别
            </el-button>
          </div>

          <!-- 可折叠详情 -->
          <el-collapse>
            <el-collapse-item title="查看原始识别文本">
              <pre class="raw-text">{{ ocrResult.raw_text }}</pre>
            </el-collapse-item>
            <el-collapse-item v-if="ocrResult.ocr_items?.length" title="查看逐行 OCR 详情">
              <el-table :data="ocrResult.ocr_items" size="small" max-height="400" stripe>
                <el-table-column prop="text" label="识别文本" show-overflow-tooltip />
                <el-table-column prop="confidence" label="置信度" width="120">
                  <template #default="{ row }">
                    <el-progress
                      :percentage="Math.round(row.confidence * 100)"
                      :color="row.confidence > 0.9 ? '#67c23a' : row.confidence > 0.7 ? '#e6a23c' : '#f56c6c'"
                      :stroke-width="14"
                      :text-inside="true"
                    />
                  </template>
                </el-table-column>
                <el-table-column v-if="rowHasPage" prop="page" label="页码" width="70" />
              </el-table>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import { recognizeFile } from '../api/ocr'
import { ElMessage } from 'element-plus'
import {
  House, DocumentAdd, Folder, Checked, User, Collection,
  Document, Search, RefreshRight,
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

function hasRole(roles) {
  return roles.includes(userStore.userInfo?.role)
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

// 文件输入
const fileInputRef = ref()
const recognizing = ref(false)

// OCR 结果
const ocrResult = ref(null)

const rowHasPage = computed(() => {
  return ocrResult.value?.ocr_items?.some(item => item.page)
})

// 选择文件后自动识别
async function onFileSelected(e) {
  const file = e.target.files[0]
  if (!file) return
  recognizing.value = true
  ocrResult.value = null
  try {
    const res = await recognizeFile(file)
    ocrResult.value = res
    ElMessage.success('识别完成')
  } catch (err) {
    ElMessage.error(err.response?.data?.message || '识别失败')
  } finally {
    recognizing.value = false
    e.target.value = ''
  }
}

function goToRegister() {
  if (!ocrResult.value?.extracted) return
  const extracted = ocrResult.value.extracted
  // 通过 query 参数传递 OCR 提取结果到立项登记页
  router.push({
    path: '/register',
    query: {
      ocr: '1',
      project_name: extracted.project_name || '',
      contract_no: extracted.contract_no || '',
      contract_amount: extracted.contract_amount || '',
      customer_name: extracted.customer_name || '',
      sign_date: extracted.sign_date || '',
    },
  })
}

function resetAll() {
  ocrResult.value = null
}
</script>

<style scoped>
.upload-area {
  padding: 24px;
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  background: #fafbfc;
  text-align: center;
}
.upload-area:hover {
  border-color: #409eff;
  background: #f0f7ff;
}
.raw-text {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.6;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
.highlight-empty {
  color: #f56c6c;
  font-style: italic;
}
</style>

<template>
  <el-container style="min-height: 100vh">
    <el-aside width="200px" style="background: #001529">
      <div style="color: #fff; text-align: center; padding: 20px; font-size: 16px; font-weight: bold">项目管理系统</div>
      <el-menu :default-active="'/projects'" background-color="#001529" text-color="#ffffffb3" active-text-color="#409eff" router>
        <el-menu-item index="/dashboard"><el-icon><House /></el-icon><span>工作台</span></el-menu-item>
        <el-menu-item index="/register"><el-icon><DocumentAdd /></el-icon><span>立项登记</span></el-menu-item>
        <el-menu-item index="/projects"><el-icon><Folder /></el-icon><span>项目档案</span></el-menu-item>
        <el-menu-item index="/ocr"><el-icon><Search /></el-icon><span>OCR 识别</span></el-menu-item>
        <el-menu-item v-if="userStore.userInfo?.role === 'admin'" index="/audit"><el-icon><Checked /></el-icon><span>立项审核</span></el-menu-item>
        <el-menu-item v-if="userStore.userInfo?.role === 'admin'" index="/users"><el-icon><User /></el-icon><span>用户管理</span></el-menu-item>
        <el-menu-item v-if="userStore.userInfo?.role === 'admin'" index="/dict"><el-icon><Collection /></el-icon><span>数据字典</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display: flex; align-items: center; border-bottom: 1px solid #e8e8e8">
        <el-button text @click="router.push('/projects')"><el-icon><ArrowLeft /></el-icon>返回</el-button>
        <span style="font-size: 18px; font-weight: 500; margin-left: 12px">项目详情 #{{ projectId }}</span>
        <el-tag :type="statusType(project.status)" style="margin-left: 12px">{{ statusLabel(project.status) }}</el-tag>
      </el-header>
      <el-main v-loading="pageLoading">
        <!-- 项目基本信息 -->
        <el-card shadow="never" style="margin-bottom: 16px">
          <template #header><span style="font-weight: 600">项目信息</span></template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="项目名称">{{ project.project_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="合同编号">{{ project.contract_no || '-' }}</el-descriptions-item>
            <el-descriptions-item label="合同金额">
              {{ project.contract_amount ? '¥' + Number(project.contract_amount).toLocaleString() : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="客户名称">{{ project.customer_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="签订日期">{{ project.sign_date || '-' }}</el-descriptions-item>
            <el-descriptions-item label="项目类型">{{ typeLabel(project.project_type) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 合同文件上传 -->
        <el-card shadow="never" style="margin-bottom: 16px">
          <template #header><span style="font-weight: 600">合同文件上传</span></template>
          <!-- 隐藏的文件输入框 -->
          <input ref="wordInputRef" type="file" accept=".docx" style="display:none" @change="onWordFileSelected" />
          <input ref="pdfInputRef" type="file" accept=".pdf" style="display:none" @change="onPdfFileSelected" />
          <el-row :gutter="24">
            <el-col :span="12">
              <div class="upload-area">
                <el-icon style="font-size: 40px; color: #409eff"><Document /></el-icon>
                <h4 style="margin: 12px 0 8px">Word 合同</h4>
                <p style="color: #999; font-size: 13px; margin: 0 0 16px">选择 .docx 文件，自动提取项目信息</p>
                <el-button type="primary" :loading="wordUploading" @click="wordInputRef.click()">
                  选择 Word 文件并解析
                </el-button>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="upload-area">
                <el-icon style="font-size: 40px; color: #e6a23c"><Document /></el-icon>
                <h4 style="margin: 12px 0 8px">盖章 PDF 合同</h4>
                <p style="color: #999; font-size: 13px; margin: 0 0 16px">选择 .pdf 文件，OCR 识别关键字段</p>
                <el-button type="warning" :loading="pdfUploading" @click="pdfInputRef.click()">
                  选择 PDF 文件并识别
                </el-button>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <!-- OCR 解析结果 -->
        <el-card v-if="ocrResult" shadow="never" style="margin-bottom: 16px">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600">OCR 解析结果</span>
              <el-tag :type="ocrResult.source === 'paddleocr' ? 'warning' : 'success'" size="small">
                {{ ocrResult.source === 'paddleocr' ? 'PaddleOCR' : 'python-docx' }}
              </el-tag>
            </div>
          </template>

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
            <el-descriptions-item label="客户名称" :span="2">
              <span :class="{ 'highlight-empty': !ocrResult.extracted?.customer_name }">
                {{ ocrResult.extracted?.customer_name || '未识别到' }}
              </span>
            </el-descriptions-item>
          </el-descriptions>

          <el-collapse>
            <el-collapse-item title="查看原始识别文本">
              <pre class="raw-text">{{ ocrResult.raw_text }}</pre>
            </el-collapse-item>
            <el-collapse-item v-if="ocrResult.ocr_items?.length" title="查看逐行 OCR 详情">
              <el-table :data="ocrResult.ocr_items" size="small" max-height="300" stripe>
                <el-table-column prop="text" label="识别文本" />
                <el-table-column prop="confidence" label="置信度" width="100">
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

        <!-- 合同校验 -->
        <el-card shadow="never" style="margin-bottom: 16px">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600">合同校验（OCR vs 录入信息）</span>
              <el-button type="primary" size="small" :loading="verifying" @click="handleVerify">
                执行校验
              </el-button>
            </div>
          </template>

          <div v-if="verifyResult === null" style="color: #999; text-align: center; padding: 20px">
            请先上传 PDF 合同，再点击"执行校验"比对 OCR 结果与录入信息
          </div>
          <div v-else-if="verifyResult.diffs?.length === 0" style="text-align: center; padding: 20px">
            <el-icon style="font-size: 48px; color: #67c23a"><CircleCheckFilled /></el-icon>
            <p style="color: #67c23c; margin-top: 8px">校验通过！OCR 识别结果与录入信息一致</p>
          </div>
          <div v-else>
            <el-alert type="warning" :closable="false" style="margin-bottom: 12px">
              发现 {{ verifyResult.diffs.length }} 处差异，请核对
            </el-alert>
            <el-table :data="verifyResult.diffs" stripe border>
              <el-table-column prop="field_name" label="字段" width="120">
                <template #default="{ row }">{{ fieldLabel(row.field_name) }}</template>
              </el-table-column>
              <el-table-column prop="ocr_value" label="OCR 识别值">
                <template #default="{ row }">
                  <span style="color: #e6a23c">{{ row.ocr_value || '(空)' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="input_value" label="录入值">
                <template #default="{ row }">
                  <span style="color: #409eff">{{ row.input_value || '(空)' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="diff_type" label="差异类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.diff_type === 'missing' ? 'info' : 'danger'" size="small">
                    {{ diffTypeLabel(row.diff_type) }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>

        <!-- 操作按钮（仅商务/管理员可提交立项，避免项目经理点击后被后端拒绝） -->
        <el-card v-if="project.status === 'draft' && canSubmit" shadow="never">
          <div style="display: flex; justify-content: flex-end; gap: 12px">
            <el-button type="primary" :loading="submitting" @click="handleSubmitProject">
              提交立项申请
            </el-button>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import {
  getProject,
  uploadWordContract,
  uploadPdfContract,
  verifyContract,
  submitProject,
} from '../api/projects'
import { ElMessage } from 'element-plus'
import {
  House, DocumentAdd, Folder, Checked, User, Collection,
  ArrowLeft, Document, CircleCheckFilled,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const projectId = Number(route.params.id)
const pageLoading = ref(false)
const project = reactive({
  project_name: '', contract_no: '', contract_amount: null,
  customer_name: '', project_type: '', sign_date: '', status: '',
})

// 文件输入框 ref
const wordInputRef = ref()
const pdfInputRef = ref()
const wordUploading = ref(false)
const pdfUploading = ref(false)

// OCR 结果
const ocrResult = ref(null)

// 校验
const verifying = ref(false)
const verifyResult = ref(null)

// 提交
const submitting = ref(false)

const rowHasPage = computed(() => {
  return ocrResult.value?.ocr_items?.some(item => item.page)
})

const statusMap = {
  draft: '草稿', pending_audit: '待审核', approved: '已立项', rejected: '已驳回', closed: '已结项',
}
const statusTypeMap = {
  draft: 'info', pending_audit: 'warning', approved: 'success', rejected: 'danger', closed: '',
}
const typeMap = {
  software: '软件开发', integration: '系统集成', consulting: '技术咨询', maintenance: '运维服务',
}
const fieldMap = {
  project_name: '项目名称', contract_amount: '合同金额', contract_no: '合同编号', sign_date: '签订日期',
}
const diffTypeMap = {
  missing: '缺失', mismatch: '不一致', format: '格式差异',
}

function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || '' }
function typeLabel(t) { return typeMap[t] || t || '-' }
function fieldLabel(f) { return fieldMap[f] || f }
function diffTypeLabel(d) { return diffTypeMap[d] || d }

// 当前角色是否可以提交立项（与后端 submit 接口的 business/admin 限制一致）
const canSubmit = computed(() =>
  ['admin', 'business'].includes(userStore.userInfo?.role)
)

// 加载项目信息（错误提示由 axios 拦截器统一处理，这里只负责兜底跳转）
async function loadProject() {
  pageLoading.value = true
  try {
    const res = await getProject(projectId)
    Object.assign(project, res)
  } catch (e) {
    router.push('/projects')
  } finally {
    pageLoading.value = false
  }
}

// 选择 Word 文件后自动上传解析（失败原因由拦截器统一弹出）
async function onWordFileSelected(e) {
  const file = e.target.files[0]
  if (!file) return
  wordUploading.value = true
  try {
    const res = await uploadWordContract(projectId, file)
    ocrResult.value = res.ocr_result
    if (res.project) {
      Object.assign(project, res.project)
    }
    ElMessage.success('Word 合同解析完成，已自动提取并回填项目信息')
  } finally {
    wordUploading.value = false
    e.target.value = ''
  }
}

// 选择 PDF 文件后自动上传识别
async function onPdfFileSelected(e) {
  const file = e.target.files[0]
  if (!file) return
  pdfUploading.value = true
  try {
    const res = await uploadPdfContract(projectId, file)
    ocrResult.value = res.ocr_result
    ElMessage.success(`PDF 合同 OCR 识别完成（版本 v${res.version}）`)
  } finally {
    pdfUploading.value = false
    e.target.value = ''
  }
}

// 合同校验
async function handleVerify() {
  verifying.value = true
  try {
    const res = await verifyContract(projectId)
    verifyResult.value = res
    if (res.diffs?.length === 0) {
      ElMessage.success('校验通过，所有字段一致')
    } else {
      ElMessage.warning(`发现 ${res.diffs.length} 处差异`)
    }
  } finally {
    verifying.value = false
  }
}

// 提交立项
async function handleSubmitProject() {
  submitting.value = true
  try {
    await submitProject(projectId)
    project.status = 'pending_audit'
    ElMessage.success('立项申请已提交')
  } finally {
    submitting.value = false
  }
}

onMounted(loadProject)
</script>

<style scoped>
.upload-area {
  padding: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #fafafa;
}
.upload-area h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #333;
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

<template>
  <el-container style="min-height: 100vh">
    <el-aside width="200px" style="background: #001529">
      <div style="color: #fff; text-align: center; padding: 20px; font-size: 16px; font-weight: bold">项目管理系统</div>
      <el-menu :default-active="'/settings'" background-color="#001529" text-color="#ffffffb3" active-text-color="#409eff" router>
        <el-menu-item index="/dashboard"><el-icon><House /></el-icon><span>工作台</span></el-menu-item>
        <el-menu-item index="/ocr"><el-icon><Search /></el-icon><span>OCR 识别</span></el-menu-item>
        <el-menu-item index="/audit"><el-icon><Checked /></el-icon><span>立项审核</span></el-menu-item>
        <el-menu-item index="/users"><el-icon><User /></el-icon><span>用户管理</span></el-menu-item>
        <el-menu-item index="/dict"><el-icon><Collection /></el-icon><span>数据字典</span></el-menu-item>
        <el-menu-item index="/settings"><el-icon><Setting /></el-icon><span>系统设置</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display: flex; align-items: center; border-bottom: 1px solid #e8e8e8">
        <span style="font-size: 18px; font-weight: 500">系统设置</span>
      </el-header>
      <el-main v-loading="loading">
        <!-- LLM 配置卡片 -->
        <el-card shadow="never" style="max-width: 720px">
          <template #header>
            <div style="display: flex; align-items: center; gap: 12px">
              <span style="font-weight: 600; font-size: 16px">🤖 LLM 智能提取配置</span>
              <el-tag :type="form.llm_enabled === 'true' ? 'success' : 'info'" size="small">
                {{ form.llm_enabled === 'true' ? '已启用' : '已关闭' }}
              </el-tag>
            </div>
          </template>

          <el-form :model="form" label-width="140px" style="max-width: 600px">
            <!-- 开关 -->
            <el-form-item label="启用 LLM 提取">
              <el-switch
                v-model="form.llm_enabled"
                active-value="true"
                inactive-value="false"
                active-text="开启"
                inactive-text="关闭"
                inline-prompt
              />
              <div style="color: #999; font-size: 12px; margin-top: 4px">
                开启后合同识别将同时使用正则 + LLM 双通道提取，LLM 结果优先
              </div>
            </el-form-item>

            <el-divider />

            <!-- API URL -->
            <el-form-item label="API 地址">
              <el-input v-model="form.llm_api_url" placeholder="https://api.example.com/v1/chat/completions" />
            </el-form-item>

            <!-- API Key -->
            <el-form-item label="API Key">
              <el-input
                v-model="form.llm_api_key"
                type="password"
                show-password
                placeholder="请输入 API Key"
              />
            </el-form-item>

            <!-- Model -->
            <el-form-item label="模型名称">
              <el-input v-model="form.llm_model" placeholder="mimo-v2.5-pro" />
            </el-form-item>

            <!-- 按钮 -->
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="handleSave">保存配置</el-button>
              <el-button :loading="testing" @click="handleTest">测试连接</el-button>
            </el-form-item>
          </el-form>

          <!-- 测试结果 -->
          <el-alert
            v-if="testResult"
            :type="testResult.success ? 'success' : 'error'"
            :title="testResult.success ? '连接成功' : '连接失败'"
            :description="testResult.success ? testResult.reply : testResult.error"
            show-icon
            style="margin-top: 16px"
          />
        </el-card>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '../api/request'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)

// 配置 id 映射，保存时需要按 id 更新
const configIdMap = {}

const form = reactive({
  llm_enabled: 'false',
  llm_api_url: '',
  llm_api_key: '',
  llm_model: '',
})

// 加载配置
async function loadConfigs() {
  loading.value = true
  try {
    const res = await request.get('/config')
    const items = res.items || []
    for (const item of items) {
      configIdMap[item.config_key] = item.id
      if (item.config_key in form) {
        form[item.config_key] = item.config_value
      }
    }
  } finally {
    loading.value = false
  }
}

// 保存配置（逐项更新）
async function handleSave() {
  saving.value = true
  try {
    const keys = ['llm_enabled', 'llm_api_url', 'llm_api_key', 'llm_model']
    for (const key of keys) {
      const id = configIdMap[key]
      if (id) {
        await request.put(`/config/${id}`, { config_value: form[key] })
      }
    }
    ElMessage.success('配置保存成功')
  } finally {
    saving.value = false
  }
}

// 测试 LLM 连通性
async function handleTest() {
  testing.value = true
  testResult.value = null
  try {
    const res = await request.post('/config/test-llm', {
      llm_api_url: form.llm_api_url,
      llm_api_key: form.llm_api_key,
      llm_model: form.llm_model,
    })
    testResult.value = res
  } catch (e) {
    testResult.value = { success: false, error: e.message || '请求失败' }
  } finally {
    testing.value = false
  }
}

onMounted(loadConfigs)
</script>

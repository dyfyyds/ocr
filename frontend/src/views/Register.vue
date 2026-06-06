<template>
  <el-container style="min-height: 100vh">
    <el-aside width="200px" style="background: #001529">
      <div style="color: #fff; text-align: center; padding: 20px; font-size: 16px; font-weight: bold">项目管理系统</div>
      <el-menu :default-active="'/register'" background-color="#001529" text-color="#ffffffb3" active-text-color="#409eff" router>
        <el-menu-item index="/dashboard"><el-icon><House /></el-icon><span>工作台</span></el-menu-item>
        <el-menu-item index="/register"><el-icon><DocumentAdd /></el-icon><span>立项登记</span></el-menu-item>
        <el-menu-item index="/projects"><el-icon><Folder /></el-icon><span>项目档案</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display: flex; align-items: center; border-bottom: 1px solid #e8e8e8">
        <span style="font-size: 18px; font-weight: 500">立项登记</span>
      </el-header>
      <el-main>
        <el-card>
          <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
            <el-form-item label="项目名称" prop="project_name">
              <el-input v-model="form.project_name" placeholder="请输入项目名称" />
            </el-form-item>
            <el-form-item label="合同编号">
              <el-input v-model="form.contract_no" placeholder="请输入合同编号" />
            </el-form-item>
            <el-form-item label="合同金额">
              <el-input-number v-model="form.contract_amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
            <el-form-item label="客户名称">
              <el-input v-model="form.customer_name" placeholder="请输入客户名称" />
            </el-form-item>
            <el-form-item label="项目类型">
              <el-select v-model="form.project_type" placeholder="请选择" style="width: 100%">
                <el-option label="软件开发" value="software" />
                <el-option label="系统集成" value="integration" />
                <el-option label="技术咨询" value="consulting" />
                <el-option label="运维服务" value="maintenance" />
              </el-select>
            </el-form-item>
            <el-form-item label="签订日期">
              <el-date-picker v-model="form.sign_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
            <el-form-item label="项目描述">
              <el-input v-model="form.description" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="handleSubmit">保存草稿</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { registerProject } from '../api/projects'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  project_name: '',
  contract_no: '',
  contract_amount: null,
  customer_name: '',
  project_type: '',
  sign_date: '',
  description: '',
})

const rules = {
  project_name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
}

async function handleSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    await registerProject(form)
    ElMessage.success('立项登记成功')
    router.push('/projects')
  } finally {
    loading.value = false
  }
}
</script>

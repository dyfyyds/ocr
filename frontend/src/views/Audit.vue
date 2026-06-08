<template>
  <el-container style="min-height: 100vh">
    <el-aside width="200px" style="background: #001529">
      <div style="color: #fff; text-align: center; padding: 20px; font-size: 16px; font-weight: bold">项目管理系统</div>
      <el-menu :default-active="'/audit'" background-color="#001529" text-color="#ffffffb3" active-text-color="#409eff" router>
        <el-menu-item index="/dashboard"><el-icon><House /></el-icon><span>工作台</span></el-menu-item>
        <el-menu-item index="/ocr"><el-icon><Search /></el-icon><span>OCR 识别</span></el-menu-item>
        <el-menu-item index="/audit"><el-icon><Checked /></el-icon><span>立项审核</span></el-menu-item>
        <el-menu-item index="/users"><el-icon><User /></el-icon><span>用户管理</span></el-menu-item>
        <el-menu-item index="/dict"><el-icon><Collection /></el-icon><span>数据字典</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display: flex; align-items: center; border-bottom: 1px solid #e8e8e8">
        <span style="font-size: 18px; font-weight: 500">立项审核</span>
      </el-header>
      <el-main>
        <el-table :data="projects" v-loading="loading" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="project_name" label="项目名称" />
          <el-table-column prop="contract_amount" label="合同金额" width="120">
            <template #default="{ row }">¥{{ Number(row.contract_amount || 0).toLocaleString() }}</template>
          </el-table-column>
          <el-table-column prop="customer_name" label="客户" />
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <el-button type="success" size="small" @click="handleAudit(row.id, 'approved')">通过</el-button>
              <el-button type="danger" size="small" @click="handleReject(row.id)">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getProjects, auditProject } from '../api/projects'
import { ElMessage, ElMessageBox } from 'element-plus'

const projects = ref([])
const loading = ref(false)

async function loadProjects() {
  loading.value = true
  try {
    const res = await getProjects({ page: 1, size: 100, status: 'pending_audit' })
    projects.value = res.items || []
  } finally {
    loading.value = false
  }
}

async function handleAudit(id, result) {
  await auditProject(id, { result })
  ElMessage.success('审核通过')
  loadProjects()
}

async function handleReject(id) {
  const { value } = await ElMessageBox.prompt('请输入驳回原因', '驳回', { inputType: 'textarea' })
  await auditProject(id, { result: 'rejected', reason: value })
  ElMessage.success('已驳回')
  loadProjects()
}

onMounted(loadProjects)
</script>

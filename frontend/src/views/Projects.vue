<template>
  <el-container style="min-height: 100vh">
    <el-aside width="200px" style="background: #001529">
      <div style="color: #fff; text-align: center; padding: 20px; font-size: 16px; font-weight: bold">项目管理系统</div>
      <el-menu :default-active="'/projects'" background-color="#001529" text-color="#ffffffb3" active-text-color="#409eff" router>
        <el-menu-item index="/dashboard"><el-icon><House /></el-icon><span>工作台</span></el-menu-item>
        <el-menu-item index="/register"><el-icon><DocumentAdd /></el-icon><span>立项登记</span></el-menu-item>
        <el-menu-item index="/projects"><el-icon><Folder /></el-icon><span>项目档案</span></el-menu-item>
        <el-menu-item v-if="userStore.userInfo?.role === 'admin'" index="/audit"><el-icon><Checked /></el-icon><span>立项审核</span></el-menu-item>
        <el-menu-item v-if="userStore.userInfo?.role === 'admin'" index="/users"><el-icon><User /></el-icon><span>用户管理</span></el-menu-item>
        <el-menu-item v-if="userStore.userInfo?.role === 'admin'" index="/dict"><el-icon><Collection /></el-icon><span>数据字典</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display: flex; align-items: center; border-bottom: 1px solid #e8e8e8">
        <span style="font-size: 18px; font-weight: 500">项目档案</span>
      </el-header>
      <el-main>
        <el-table :data="projects" v-loading="loading" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="project_name" label="项目名称" />
          <el-table-column prop="contract_no" label="合同编号" />
          <el-table-column prop="contract_amount" label="合同金额" width="120">
            <template #default="{ row }">¥{{ Number(row.contract_amount || 0).toLocaleString() }}</template>
          </el-table-column>
          <el-table-column prop="customer_name" label="客户" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" />
        </el-table>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../store/user'
import { getProjects } from '../api/projects'

const userStore = useUserStore()
const projects = ref([])
const loading = ref(false)

const statusMap = {
  draft: '草稿', pending_audit: '待审核', approved: '已立项', rejected: '已驳回', closed: '已结项',
}
const statusTypeMap = {
  draft: 'info', pending_audit: 'warning', approved: 'success', rejected: 'danger', closed: '',
}

function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || '' }

onMounted(async () => {
  loading.value = true
  try {
    const res = await getProjects({ page: 1, size: 100 })
    projects.value = res.items || []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <el-container style="min-height: 100vh">
    <el-aside width="200px" style="background: #001529">
      <div style="color: #fff; text-align: center; padding: 20px; font-size: 16px; font-weight: bold">项目管理系统</div>
      <el-menu :default-active="'/users'" background-color="#001529" text-color="#ffffffb3" active-text-color="#409eff" router>
        <el-menu-item index="/dashboard"><el-icon><House /></el-icon><span>工作台</span></el-menu-item>
        <el-menu-item index="/audit"><el-icon><Checked /></el-icon><span>立项审核</span></el-menu-item>
        <el-menu-item index="/users"><el-icon><User /></el-icon><span>用户管理</span></el-menu-item>
        <el-menu-item index="/dict"><el-icon><Collection /></el-icon><span>数据字典</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e8e8e8">
        <span style="font-size: 18px; font-weight: 500">用户管理</span>
        <el-button type="primary" @click="showDialog = true">新增用户</el-button>
      </el-header>
      <el-main>
        <el-table :data="users" v-loading="loading" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="real_name" label="姓名" />
          <el-table-column prop="role" label="角色" width="100">
            <template #default="{ row }">
              <el-tag>{{ roleLabel(row.role) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button size="small" @click="toggleStatus(row)">{{ row.status === 1 ? '禁用' : '启用' }}</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 新增用户弹窗 -->
        <el-dialog v-model="showDialog" title="新增用户" width="500">
          <el-form ref="userFormRef" :model="userForm" :rules="userRules" label-width="80px">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="userForm.username" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="userForm.password" type="password" show-password />
            </el-form-item>
            <el-form-item label="姓名">
              <el-input v-model="userForm.real_name" />
            </el-form-item>
            <el-form-item label="角色" prop="role">
              <el-select v-model="userForm.role" style="width: 100%">
                <el-option label="管理员" value="admin" />
                <el-option label="商务" value="business" />
                <el-option label="财务" value="finance" />
                <el-option label="项目经理" value="pm" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showDialog = false">取消</el-button>
            <el-button type="primary" @click="handleCreate">确定</el-button>
          </template>
        </el-dialog>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '../api/request'
import { ElMessage } from 'element-plus'

const users = ref([])
const loading = ref(false)
const showDialog = ref(false)
const userFormRef = ref()

const userForm = reactive({ username: '', password: '', real_name: '', role: '' })
const userRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

const roleMap = { admin: '管理员', business: '商务', finance: '财务', pm: '项目经理' }
function roleLabel(r) { return roleMap[r] || r }

async function loadUsers() {
  loading.value = true
  try {
    const res = await request.get('/users', { params: { page: 1, size: 100 } })
    users.value = res.items || []
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  await userFormRef.value.validate()
  await request.post('/users', userForm)
  ElMessage.success('创建成功')
  showDialog.value = false
  Object.assign(userForm, { username: '', password: '', real_name: '', role: '' })
  loadUsers()
}

async function toggleStatus(user) {
  await request.put(`/users/${user.id}/status`)
  ElMessage.success('操作成功')
  loadUsers()
}

onMounted(loadUsers)
</script>

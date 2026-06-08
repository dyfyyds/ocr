<template>
  <el-container style="min-height: 100vh">
    <el-aside width="200px" style="background: #001529">
      <div style="color: #fff; text-align: center; padding: 20px; font-size: 16px; font-weight: bold">
        项目管理系统
      </div>
      <el-menu
        :default-active="activeMenu"
        background-color="#001529"
        text-color="#ffffffb3"
        active-text-color="#409eff"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><House /></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item v-if="hasRole(['admin', 'business'])" index="/register">
          <el-icon><DocumentAdd /></el-icon>
          <span>立项登记</span>
        </el-menu-item>
        <el-menu-item v-if="hasRole(['admin', 'business'])" index="/projects">
          <el-icon><Folder /></el-icon>
          <span>项目档案</span>
        </el-menu-item>
        <el-menu-item index="/ocr">
          <el-icon><Search /></el-icon>
          <span>OCR 识别</span>
        </el-menu-item>
        <el-menu-item v-if="hasRole(['admin'])" index="/audit">
          <el-icon><Checked /></el-icon>
          <span>立项审核</span>
        </el-menu-item>
        <el-menu-item v-if="hasRole(['admin'])" index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item v-if="hasRole(['admin'])" index="/dict">
          <el-icon><Collection /></el-icon>
          <span>数据字典</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e8e8e8">
        <span style="font-size: 18px; font-weight: 500">工作台</span>
        <div>
          <span style="margin-right: 16px">{{ userStore.userInfo?.real_name || userStore.userInfo?.username }}</span>
          <el-button type="danger" text @click="handleLogout">退出</el-button>
        </div>
      </el-header>

      <el-main>
        <!-- 统计卡片 -->
        <el-row :gutter="20" style="margin-bottom: 20px">
          <el-col :span="6" v-for="card in statCards" :key="card.label">
            <el-card shadow="hover">
              <div style="text-align: center">
                <div style="font-size: 28px; font-weight: bold; color: #409eff">{{ card.value }}</div>
                <div style="color: #909399; margin-top: 8px">{{ card.label }}</div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 项目状态分布 -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card header="项目状态分布">
              <div ref="statusChart" style="height: 300px"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card header="最近活动">
              <el-timeline>
                <el-timeline-item
                  v-for="log in recentLogs"
                  :key="log.id"
                  :timestamp="log.created_at"
                  placement="top"
                >
                  {{ log.detail }}
                </el-timeline-item>
              </el-timeline>
              <el-empty v-if="!recentLogs.length" description="暂无活动" />
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import request from '../api/request'
import * as echarts from 'echarts'

const router = useRouter()
const userStore = useUserStore()

const activeMenu = ref('/dashboard')
const stats = ref({})
const recentLogs = ref([])
const statusChart = ref(null)

const statCards = computed(() => [
  { label: '项目总数', value: stats.value.project_total || 0 },
  { label: '已立项', value: stats.value.approved_total || 0 },
  { label: '开票总额', value: `¥${(stats.value.invoice_total || 0).toLocaleString()}` },
  { label: '回款总额', value: `¥${(stats.value.payment_total || 0).toLocaleString()}` },
])

function hasRole(roles) {
  return roles.includes(userStore.userInfo?.role)
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

async function loadDashboard() {
  try {
    const [statsRes, logsRes, distRes] = await Promise.all([
      request.get('/dashboard/stats'),
      request.get('/dashboard/recent-logs'),
      request.get('/dashboard/status-distribution'),
    ])
    stats.value = statsRes
    recentLogs.value = logsRes.items || []

    // 渲染饼图
    if (statusChart.value && distRes.items?.length) {
      const chart = echarts.init(statusChart.value)
      const statusNames = { draft: '草稿', pending_audit: '待审核', approved: '已立项', rejected: '已驳回', closed: '已结项' }
      chart.setOption({
        tooltip: { trigger: 'item' },
        series: [{
          type: 'pie',
          radius: '60%',
          data: distRes.items.map(item => ({
            name: statusNames[item.status] || item.status,
            value: item.count,
          })),
        }],
      })
    }
  } catch {
    // 错误已在拦截器处理
  }
}

onMounted(async () => {
  await userStore.fetchUser()
  loadDashboard()
})
</script>

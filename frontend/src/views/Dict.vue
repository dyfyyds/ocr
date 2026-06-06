<template>
  <el-container style="min-height: 100vh">
    <el-aside width="200px" style="background: #001529">
      <div style="color: #fff; text-align: center; padding: 20px; font-size: 16px; font-weight: bold">项目管理系统</div>
      <el-menu :default-active="'/dict'" background-color="#001529" text-color="#ffffffb3" active-text-color="#409eff" router>
        <el-menu-item index="/dashboard"><el-icon><House /></el-icon><span>工作台</span></el-menu-item>
        <el-menu-item index="/audit"><el-icon><Checked /></el-icon><span>立项审核</span></el-menu-item>
        <el-menu-item index="/users"><el-icon><User /></el-icon><span>用户管理</span></el-menu-item>
        <el-menu-item index="/dict"><el-icon><Collection /></el-icon><span>数据字典</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display: flex; align-items: center; border-bottom: 1px solid #e8e8e8">
        <span style="font-size: 18px; font-weight: 500">数据字典</span>
      </el-header>
      <el-main>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card header="字典类型">
              <el-table :data="dictTypes" size="small">
                <el-table-column prop="type_code" label="编码" />
                <el-table-column prop="type_name" label="名称" />
              </el-table>
            </el-card>
          </el-col>
          <el-col :span="16">
            <el-card header="字典项">
              <el-table :data="dictItems" size="small">
                <el-table-column prop="item_label" label="标签" />
                <el-table-column prop="item_value" label="值" />
                <el-table-column prop="sort_order" label="排序" width="80" />
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../api/request'

const dictTypes = ref([])
const dictItems = ref([])

onMounted(async () => {
  const res = await request.get('/dict/types')
  dictTypes.value = res.items || []

  // 加载第一个类型的字典项
  if (dictTypes.value.length) {
    const itemsRes = await request.get(`/dict/types/${dictTypes.value[0].type_code}/items`)
    dictItems.value = itemsRes.items || []
  }
})
</script>

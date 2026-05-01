<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { adminListScores } from '../../api'

const router = useRouter()
const scores = ref([])
const loading = ref(false)

function getColor(v) { if (v>=85) return '#34c759'; if (v>=70) return '#007aff'; if (v>=50) return '#ff9500'; return '#ff3b30' }
function getTag(v) { if (v>=85) return ''; if (v>=70) return 'success'; if (v>=50) return 'warning'; return 'danger' }

function fmtTime(d) {
  if (!d) return ''
  const s = String(d)
  // 后端返回裸 UTC 时间（无时区标记），追加 Z 强制按 UTC 解析再转本地
  const date = s.endsWith('Z') || s.includes('+') ? new Date(s) : new Date(s + 'Z')
  return date.toLocaleString('zh-CN')
}

async function load() {
  loading.value = true
  try { const r = await adminListScores({ page_size: 100 }); scores.value = r.data } catch {} finally { loading.value = false }
}
onMounted(load)
</script>

<template>
  <div class="glass-panel admin-page-panel">
    <div class="table-wrap">
      <el-table :data="scores" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="55" align="center" />
        <el-table-column label="剧本/用户" min-width="110">
          <template #default="{row}"><span style="font-size:12px;color:var(--text-tertiary);">剧本#{{ row.script_id }} / 用户#{{ row.user_id }}</span></template>
        </el-table-column>
        <el-table-column label="模型" min-width="150">
          <template #default="{row}"><span style="font-size:13px;">{{ row.provider||'-' }} / {{ row.model_name||'-' }}</span></template>
        </el-table-column>
        <el-table-column label="综合" width="80" align="center">
          <template #default="{row}"><el-tag :type="getTag(row.overall)" effect="light" size="small"><b>{{ row.overall }}</b></el-tag></template>
        </el-table-column>
        <el-table-column label="有趣" width="55" align="center">
          <template #default="{row}"><span :style="`color:${getColor(row.interestingness)}`">{{ row.interestingness }}</span></template>
        </el-table-column>
        <el-table-column label="热门" width="55" align="center">
          <template #default="{row}"><span :style="`color:${getColor(row.popularity)}`">{{ row.popularity }}</span></template>
        </el-table-column>
        <el-table-column label="逻辑" width="55" align="center">
          <template #default="{row}"><span :style="`color:${getColor(row.logic)}`">{{ row.logic }}</span></template>
        </el-table-column>
        <el-table-column label="动作" width="55" align="center">
          <template #default="{row}"><span :style="`color:${getColor(row.action_smoothness)}`">{{ row.action_smoothness }}</span></template>
        </el-table-column>
        <el-table-column label="剧情" width="55" align="center">
          <template #default="{row}"><span :style="`color:${getColor(row.plot_smoothness)}`">{{ row.plot_smoothness }}</span></template>
        </el-table-column>
        <el-table-column prop="points_cost" label="消耗" width="55" align="center">
          <template #default="{row}"><span style="font-size:12px;color:var(--text-tertiary);">{{ row.points_cost }}</span></template>
        </el-table-column>
        <el-table-column label="时间" width="170">
          <template #default="{row}"><span style="font-size:13px;">{{ fmtTime(row.created_at) }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right" align="center">
          <template #default="{row}"><el-button size="small" type="primary" @click="router.push(`/score/${row.id}`)">查看</el-button></template>
        </el-table-column>
      </el-table>
    </div>
    <div v-if="!loading && scores.length===0" class="empty-state">
      <div class="empty-icon"><el-icon :size="36"><FolderOpened /></el-icon></div>
      <p>暂无评分记录</p>
    </div>
  </div>
</template>

<style scoped>
.admin-page-panel { overflow: hidden; }
.table-wrap { overflow-x: auto; }
</style>

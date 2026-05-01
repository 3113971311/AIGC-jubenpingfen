<script setup>
import { ref, onMounted } from 'vue'
import { getPointsLog } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const logs = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const r = await getPointsLog({ page_size: 100 })
    logs.value = r.data
  } catch {} finally { loading.value = false }
})

function fmtDate(d) {
  if (!d) return ''
  const s = String(d)
  const date = s.endsWith('Z') || s.includes('+') ? new Date(s) : new Date(s + 'Z')
  return date.toLocaleString('zh-CN')
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">积分明细</h1>
      <p class="page-subtitle">当前余额 <strong style="color:var(--accent);">{{ auth.points }}</strong> 积分</p>
    </div>

    <div v-if="loading" class="glass-card empty-state"><p>加载中...</p></div>

    <div v-else-if="logs.length === 0" class="glass-card empty-state">
      <div class="empty-icon"><el-icon :size="36"><Coin /></el-icon></div>
      <p>暂无积分记录</p>
    </div>

    <div v-else class="logs-list">
      <div v-for="item in logs" :key="item.id" class="log-item glass-card">
        <div class="log-left">
          <div class="log-reason">{{ item.reason }}</div>
          <div class="log-time">{{ fmtDate(item.created_at) }}</div>
        </div>
        <div class="log-right">
          <span class="log-amount" :class="item.amount > 0 ? 'income' : 'expense'">
            {{ item.amount > 0 ? '+' : '' }}{{ item.amount }}
          </span>
          <span class="log-balance">余额 {{ item.balance_after }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.logs-list { display: flex; flex-direction: column; gap: 10px; }

.log-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 22px; gap: 16px;
}
.log-left { min-width: 0; flex: 1; }
.log-reason { font-size: 14px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.log-time { font-size: 12px; color: var(--text-tertiary); margin-top: 4px; }
.log-right { text-align: right; flex-shrink: 0; }
.log-amount { font-size: 18px; font-weight: 700; display: block; }
.log-amount.income { color: var(--green); }
.log-amount.expense { color: var(--red); }
.log-balance { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; display: block; }

@media (max-width: 480px) {
  .log-item { flex-direction: column; align-items: flex-start; }
  .log-right { text-align: left; }
  .log-reason { white-space: normal; }
}
</style>

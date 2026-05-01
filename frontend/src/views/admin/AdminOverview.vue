<script setup>
import { ref, onMounted } from 'vue'
import { adminGetStats } from '../../api'

const stats = ref({ total_users: 0, total_scores: 0, total_points_consumed: 0 })
const loading = ref(true)

const cards = [
  { key: 'total_users', label: '总用户数', icon: 'User', color: '#007aff' },
  { key: 'total_scores', label: '总评分次数', icon: 'DataLine', color: '#5856d6' },
  { key: 'total_points_consumed', label: '总积分消耗', icon: 'Coin', color: '#ff9500' },
]

onMounted(async () => {
  try {
    const res = await adminGetStats()
    stats.value = res.data
  } catch {} finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-loading="loading">
    <div class="stats-grid">
      <div v-for="(c, i) in cards" :key="c.key" class="glass-card stat-card" :style="`animation-delay:${i * 0.08}s`">
        <div class="stat-icon" :style="{ background: c.color + '15', color: c.color }">
          <el-icon :size="26"><component :is="c.icon" /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value" :style="{ color: c.color }">{{ stats[c.key]?.toLocaleString() || '0' }}</div>
          <div class="stat-label">{{ c.label }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
}

.stat-card {
  padding: 28px;
  display: flex;
  align-items: center;
  gap: 20px;
  animation: fadeInUp 0.5s ease both;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-body {
  min-width: 0;
}

.stat-value {
  font-size: 38px;
  font-weight: 700;
  letter-spacing: -1px;
  line-height: 1.1;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}
</style>

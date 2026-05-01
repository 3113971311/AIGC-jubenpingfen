<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getScore, getScript } from '../api'
import RadarChart from '../components/RadarChart.vue'

const route = useRoute()
const score = ref(null)
const script = ref(null)
const loading = ref(true)

const radarData = computed(() => {
  if (!score.value) return null
  return {
    labels: ['有趣度', '热门度', '逻辑程度', '动作链流畅', '剧情发展流畅'],
    values: [score.value.interestingness, score.value.popularity, score.value.logic, score.value.action_smoothness, score.value.plot_smoothness],
  }
})

const dimensionDetails = computed(() => {
  if (!score.value) return []
  return [
    { label: '有趣度', value: score.value.interestingness, icon: 'StarFilled', color: '#ff9500', desc: '故事吸引力与人物塑造' },
    { label: '热门度', value: score.value.popularity, icon: 'TrendCharts', color: '#ff3b30', desc: '市场热度与商业潜力' },
    { label: '逻辑程度', value: score.value.logic, icon: 'Cpu', color: '#007aff', desc: '剧情设定与行为自洽' },
    { label: '动作链流畅', value: score.value.action_smoothness, icon: 'MagicStick', color: '#5856d6', desc: '动作场景衔接与节奏' },
    { label: '剧情发展流畅', value: score.value.plot_smoothness, icon: 'DataLine', color: '#34c759', desc: '整体剧情推进顺畅度' },
  ]
})

function getScoreColor(v) {
  if (v >= 85) return '#34c759'; if (v >= 70) return '#007aff'
  if (v >= 50) return '#ff9500'; return '#ff3b30'
}

onMounted(async () => {
  try {
    const id = parseInt(route.params.id)
    try { const r = await getScore(id); score.value = r.data; const s = await getScript(r.data.script_id); script.value = s.data }
    catch { const s = await getScript(id); script.value = s.data }
  } catch {} finally { loading.value = false }
})

function fmtDate(d) {
  if (!d) return ''
  const s = String(d)
  const date = s.endsWith('Z') || s.includes('+') ? new Date(s) : new Date(s + 'Z')
  return date.toLocaleString('zh-CN')
}

// 将 AI 返回的类 Markdown 文本转为 HTML
function renderContent(text) {
  if (!text) return ''
  let html = text
  // 处理 Unicode 表格块 → HTML table
  html = html.replace(/((?:^[┌├└┼┬┴─│].*\n?)+)/gm, (block) => {
    const lines = block.trim().split('\n')
    const rows = []
    for (const line of lines) {
      // 跳过分隔线 (┌─ ├─ └─ 等)
      if (/[┌├└┼]/.test(line.replace(/[─┬┴]/g, ''))) continue
      // 提取 │ 分隔的单元格
      const cells = line.split('│').map(c => c.trim()).filter(c => c)
      if (cells.length) {
        const isHeader = rows.length === 0
        const tag = isHeader ? 'th' : 'td'
        rows.push(`<tr>${cells.map(c => `<${tag}>${c}</${tag}>`).join('')}</tr>`)
      }
    }
    return `<table class="md-table"><tbody>${rows.join('')}</tbody></table>`
  })
  // **粗体**
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // ### 标题
  html = html.replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>')
  // 列表组（连续 * xxx 或 - xxx 行，但不含表格行）
  html = html.replace(/((?:^[\*\-] .+\n?)+)/gm, (block) => {
    const items = block.trim().split('\n').map(l => `<li>${l.replace(/^[\*\-] /, '')}</li>`).join('')
    return `<ul class="md-list">${items}</ul>`
  })
  // 剩余换行 → <br>
  html = html.replace(/\n/g, '<br>')
  return html
}
</script>

<template>
  <div class="page-container">
    <div v-if="loading" class="glass-card empty-state"><p>加载中...</p></div>

    <template v-else-if="score && script">
      <div class="page-header">
        <h1 class="page-title">{{ script.title }}</h1>
        <p class="page-subtitle">
          {{ fmtDate(score.created_at) }}
        </p>
      </div>

      <!-- Overall + Radar 同行 -->
      <div class="score-top-row">
        <div class="overall-card glass-card">
          <span class="overall-label">综合评分</span>
          <div class="overall-value" :style="{color:getScoreColor(score.overall)}">{{ score.overall }}</div>
          <span class="overall-max">满分 100</span>
        </div>

        <div class="glass-card radar-card">
          <RadarChart v-if="radarData" :labels="radarData.labels" :values="radarData.values" />
        </div>
      </div>

      <!-- Dimensions -->
      <div class="dims-grid">
        <div v-for="d in dimensionDetails" :key="d.label" class="dim-card glass-card">
          <div class="dim-header">
            <el-icon :size="20" :style="{color:d.color}"><component :is="d.icon" /></el-icon>
            <span class="dim-label">{{ d.label }}</span>
          </div>
          <div class="dim-value" :style="{color:getScoreColor(d.value)}">{{ d.value }}</div>
          <p class="dim-desc">{{ d.desc }}</p>
        </div>
      </div>

      <!-- Analysis -->
      <div v-if="score.analysis" class="glass-card analysis-card">
        <h3 class="analysis-title">AI 综合分析</h3>
        <div class="analysis-body" v-html="renderContent(score.analysis)" />
      </div>

      <!-- Suggestions -->
      <div v-if="score.suggestions" class="glass-card analysis-card" style="margin-top:16px;">
        <h3 class="analysis-title" style="color:var(--accent);">改进建议</h3>
        <div class="analysis-body" v-html="renderContent(score.suggestions)" />
      </div>
    </template>

    <template v-else-if="script && !score">
      <div class="glass-card empty-state">
        <div class="empty-icon"><el-icon :size="40"><Document /></el-icon></div>
        <h2 style="margin-top:8px;">{{ script.title }}</h2>
        <p style="margin-top:4px;">字数: {{ script.char_count.toLocaleString() }} · 尚未评分</p>
      </div>
    </template>

    <template v-else>
      <div class="glass-card empty-state">
        <div class="empty-icon"><el-icon :size="40"><Warning /></el-icon></div>
        <p>未找到相关记录</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.overall-card { padding: 28px 20px; text-align: center; flex: 0 0 220px; display: flex; flex-direction: column; justify-content: center; }
.overall-label { font-size: 13px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; }
.overall-value { font-size: 56px; font-weight: 700; letter-spacing: -2px; line-height: 1.1; }
.overall-max { font-size: 14px; color: var(--text-tertiary); }

.score-top-row {
  display: flex; gap: 20px; margin-bottom: 24px; align-items: stretch;
}
.radar-card {
  flex: 1; padding: 20px; display: flex; align-items: center; justify-content: center;
  min-width: 0;
}

.dims-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 16px; margin-bottom: 24px; }
.dim-card { padding: 22px; }
.dim-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.dim-label { font-weight: 600; }
.dim-value { font-size: 42px; font-weight: 700; letter-spacing: -1px; }
.dim-desc { font-size: 13px; color: var(--text-secondary); }

.analysis-card { padding: 24px; }
.analysis-title { font-weight: 600; margin-bottom: 14px; font-size: 16px; }
.analysis-body { color: var(--text-secondary); line-height: 1.8; font-size: 14px; }
.analysis-body :deep(.md-table) {
  width: 100%; border-collapse: collapse; margin: 12px 0;
  font-size: 13px; border-radius: 10px; overflow: hidden;
  border: 1px solid rgba(0,0,0,0.06);
}
.analysis-body :deep(.md-table th) {
  background: rgba(0,0,0,0.03); font-weight: 600; text-align: center;
  padding: 10px 12px; border-bottom: 1px solid rgba(0,0,0,0.06);
  white-space: nowrap;
}
.analysis-body :deep(.md-table td) {
  padding: 10px 12px; border-bottom: 1px solid rgba(0,0,0,0.04);
  vertical-align: top;
}
.analysis-body :deep(.md-table td:first-child),
.analysis-body :deep(.md-table th:first-child) { text-align: center; white-space: nowrap; font-weight: 500; }
.analysis-body :deep(.md-table td:nth-child(2)),
.analysis-body :deep(.md-table th:nth-child(2)) { text-align: center; white-space: nowrap; }
.analysis-body :deep(.md-table tr:last-child td) {
  border-bottom: none; font-weight: 600; background: rgba(0,122,255,0.03);
}
.analysis-body :deep(.md-h4) { font-size: 15px; font-weight: 600; margin: 16px 0 8px; color: var(--text-primary); }
.analysis-body :deep(.md-list) { margin: 8px 0; padding-left: 20px; }
.analysis-body :deep(.md-list li) { margin-bottom: 6px; }
.analysis-body :deep(strong) { color: var(--text-primary); }

@media (max-width: 768px) {
  .overall-value { font-size: 56px; }
  .dims-grid { grid-template-columns: repeat(2, 1fr); }
  .dim-value { font-size: 32px; }
  .score-top-row { flex-direction: column; }
  .overall-card { flex: 0 0 auto; }
  .analysis-body :deep(.md-table) { font-size: 12px; }
  .analysis-body :deep(.md-table th),
  .analysis-body :deep(.md-table td) { padding: 8px 10px; }
}
</style>

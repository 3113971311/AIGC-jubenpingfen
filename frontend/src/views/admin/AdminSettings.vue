<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminGetSettings, adminUpdateSettings, getActiveModels } from '../../api'

const loading = ref(false)
const saving = ref(false)
const models = ref([])

const form = reactive({
  max_chars: 100000,
  points_per_10000_chars: 1,
  active_model_id: '',
  score_timeout: 300,
})

onMounted(async () => {
  loading.value = true
  try {
    const [settingsRes, modelsRes] = await Promise.all([
      adminGetSettings(),
      getActiveModels(),
    ])
    models.value = modelsRes.data
    for (const item of settingsRes.data) {
      const v = parseInt(item.value)
      if (item.key === 'max_chars') form.max_chars = isNaN(v) ? 100000 : v
      if (item.key === 'points_per_10000_chars') form.points_per_10000_chars = isNaN(v) ? 1 : v
      if (item.key === 'active_model_id') form.active_model_id = item.value || ''
      if (item.key === 'score_timeout') form.score_timeout = isNaN(v) ? 300 : v
    }
  } catch {} finally { loading.value = false }
})

async function handleSave() {
  saving.value = true
  try {
    await adminUpdateSettings([
      { key: 'max_chars', value: String(form.max_chars) },
      { key: 'points_per_10000_chars', value: String(form.points_per_10000_chars) },
      { key: 'active_model_id', value: form.active_model_id },
      { key: 'score_timeout', value: String(form.score_timeout) },
    ])
    ElMessage.success('设置已保存')
  } catch {} finally { saving.value = false }
}
</script>

<template>
  <div class="glass-card" style="padding:0;overflow:hidden;" v-loading="loading">
    <div class="setting-row">
      <div class="setting-row-left">
        <div class="setting-row-icon" style="background:rgba(0,122,255,0.1);color:#007aff;">
          <el-icon :size="22"><EditPen /></el-icon>
        </div>
        <div class="setting-row-body">
          <div class="setting-row-title">剧本最大字数</div>
          <div class="setting-row-desc">设为 0 则不限制</div>
        </div>
      </div>
      <div class="setting-row-right">
        <el-input-number v-model="form.max_chars" :min="0" :max="1000000" :step="10000" :controls="false" size="large" style="width:180px;" />
        <span class="setting-row-hint">{{ form.max_chars === 0 ? '不限制' : form.max_chars.toLocaleString() + ' 字' }}</span>
      </div>
    </div>

    <div class="setting-divider" />

    <div class="setting-row">
      <div class="setting-row-left">
        <div class="setting-row-icon" style="background:rgba(52,199,89,0.1);color:#34c759;">
          <el-icon :size="22"><Money /></el-icon>
        </div>
        <div class="setting-row-body">
          <div class="setting-row-title">每万字消耗积分</div>
          <div class="setting-row-desc">⌈字数 ÷ 10000⌉ × 此值</div>
        </div>
      </div>
      <div class="setting-row-right">
        <el-input-number v-model="form.points_per_10000_chars" :min="1" :max="100" :step="1" :controls="false" size="large" style="width:120px;" />
        <span class="setting-row-hint">1.5万字 = {{ 2 * form.points_per_10000_chars }} 积分</span>
      </div>
    </div>

    <div class="setting-divider" />

    <div class="setting-row">
      <div class="setting-row-left">
        <div class="setting-row-icon" style="background:rgba(88,86,214,0.1);color:#5856d6;">
          <el-icon :size="22"><Cpu /></el-icon>
        </div>
        <div class="setting-row-body">
          <div class="setting-row-title">评分模型</div>
          <div class="setting-row-desc">用户评分时使用的 AI 模型</div>
        </div>
      </div>
      <div class="setting-row-right">
        <el-select v-model="form.active_model_id" placeholder="选择模型" style="width:260px;" size="large">
          <el-option v-for="m in models" :key="m.id" :label="`${m.provider} / ${m.model_name}`" :value="String(m.id)" />
        </el-select>
      </div>
    </div>

    <div class="setting-divider" />

    <div class="setting-row">
      <div class="setting-row-left">
        <div class="setting-row-icon" style="background:rgba(255,149,0,0.1);color:#ff9500;">
          <el-icon :size="22"><Timer /></el-icon>
        </div>
        <div class="setting-row-body">
          <div class="setting-row-title">AI 评分超时（秒）</div>
          <div class="setting-row-desc">AI 调用超时时间，建议 180-600 秒</div>
        </div>
      </div>
      <div class="setting-row-right">
        <el-input-number v-model="form.score_timeout" :min="0" :max="3600" :step="30" :controls="false" size="large" style="width:120px;" />
        <span class="setting-row-hint">{{ form.score_timeout === 0 ? '不限制' : Math.round(form.score_timeout / 60) + ' 分钟' }}</span>
      </div>
    </div>

    <div class="setting-footer">
      <div style="flex:1" />
      <button class="glass-btn glass-btn-primary" @click="handleSave" :disabled="saving" style="padding:10px 36px;">
        {{ saving ? '保存中...' : '保存' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.setting-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 24px 28px; gap: 24px; flex-wrap: wrap;
}
.setting-row-left { display: flex; align-items: center; gap: 16px; min-width: 0; flex: 1; }
.setting-row-icon {
  width: 44px; height: 44px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.setting-row-body { min-width: 0; }
.setting-row-title { font-size: 15px; font-weight: 600; }
.setting-row-desc { font-size: 13px; color: var(--text-secondary); margin-top: 3px; }
.setting-row-right { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.setting-row-hint { font-size: 12px; color: var(--text-tertiary); white-space: nowrap; }
.setting-divider { height: 1px; background: rgba(0,0,0,0.05); margin: 0 28px; }
.setting-footer { padding: 20px 28px; background: rgba(0,0,0,0.015); display: flex; }

@media (max-width: 640px) {
  .setting-row { flex-direction: column; align-items: flex-start; }
  .setting-row-right { padding-left: 60px; }
}
</style>

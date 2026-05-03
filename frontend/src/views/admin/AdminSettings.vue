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
  smtp_host: 'smtp.qq.com',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  smtp_use_tls: true,
  feedback_recipient: '',
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
      const v = item.value
      const n = parseInt(v)
      if (item.key === 'max_chars') form.max_chars = isNaN(n) ? 100000 : n
      if (item.key === 'points_per_10000_chars') form.points_per_10000_chars = isNaN(n) ? 1 : n
      if (item.key === 'active_model_id') form.active_model_id = v || ''
      if (item.key === 'score_timeout') form.score_timeout = isNaN(n) ? 300 : n
      if (item.key === 'smtp_host') form.smtp_host = v || 'smtp.qq.com'
      if (item.key === 'smtp_port') form.smtp_port = isNaN(n) ? 587 : n
      if (item.key === 'smtp_username') form.smtp_username = v || ''
      if (item.key === 'smtp_password') form.smtp_password = v || ''
      if (item.key === 'smtp_use_tls') form.smtp_use_tls = v === 'true'
      if (item.key === 'feedback_recipient') form.feedback_recipient = v || ''
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
      { key: 'smtp_host', value: form.smtp_host },
      { key: 'smtp_port', value: String(form.smtp_port) },
      { key: 'smtp_username', value: form.smtp_username },
      { key: 'smtp_password', value: form.smtp_password },
      { key: 'smtp_use_tls', value: form.smtp_use_tls ? 'true' : 'false' },
      { key: 'feedback_recipient', value: form.feedback_recipient },
    ])
    ElMessage.success('设置已保存')
  } catch {} finally { saving.value = false }
}
</script>

<template>
  <div class="glass-card" style="padding:0;overflow:hidden;" v-loading="loading">
    <!-- 剧本最大字数 -->
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

    <!-- 每万字消耗积分 -->
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

    <!-- 评分模型 -->
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

    <!-- AI 评分超时 -->
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

    <div class="setting-divider" />

    <!-- 反馈邮箱设置标题 -->
    <div style="padding:20px 28px 0;">
      <div style="font-size:15px;font-weight:600;">反馈邮箱设置</div>
      <div style="font-size:13px;color:var(--text-secondary);margin-top:3px;">用户提交反馈时使用的邮件通知配置</div>
    </div>

    <!-- SMTP 服务器 -->
    <div class="setting-row">
      <div class="setting-row-left">
        <div class="setting-row-icon" style="background:rgba(0,122,255,0.1);color:#007aff;">
          <el-icon :size="22"><Message /></el-icon>
        </div>
        <div class="setting-row-body">
          <div class="setting-row-title">SMTP 服务器</div>
          <div class="setting-row-desc">如 smtp.qq.com、smtp.163.com</div>
        </div>
      </div>
      <div class="setting-row-right">
        <el-input v-model="form.smtp_host" placeholder="smtp.qq.com" size="large" style="width:220px;" />
      </div>
    </div>

    <div class="setting-divider" />

    <!-- SMTP 端口 -->
    <div class="setting-row">
      <div class="setting-row-left">
        <div class="setting-row-icon" style="background:rgba(0,122,255,0.1);color:#007aff;">
          <el-icon :size="22"><Position /></el-icon>
        </div>
        <div class="setting-row-body">
          <div class="setting-row-title">SMTP 端口</div>
          <div class="setting-row-desc">QQ/163 邮箱通常用 587</div>
        </div>
      </div>
      <div class="setting-row-right">
        <el-input-number v-model="form.smtp_port" :min="1" :max="65535" :step="1" :controls="false" size="large" style="width:120px;" />
      </div>
    </div>

    <div class="setting-divider" />

    <!-- 发件邮箱 -->
    <div class="setting-row">
      <div class="setting-row-left">
        <div class="setting-row-icon" style="background:rgba(0,122,255,0.1);color:#007aff;">
          <el-icon :size="22"><User /></el-icon>
        </div>
        <div class="setting-row-body">
          <div class="setting-row-title">发件邮箱</div>
          <div class="setting-row-desc">SMTP 登录账号</div>
        </div>
      </div>
      <div class="setting-row-right">
        <el-input v-model="form.smtp_username" placeholder="your@qq.com" size="large" style="width:240px;" />
      </div>
    </div>

    <div class="setting-divider" />

    <!-- 授权码 / 密码 -->
    <div class="setting-row">
      <div class="setting-row-left">
        <div class="setting-row-icon" style="background:rgba(0,122,255,0.1);color:#007aff;">
          <el-icon :size="22"><Lock /></el-icon>
        </div>
        <div class="setting-row-body">
          <div class="setting-row-title">授权码 / 密码</div>
          <div class="setting-row-desc">QQ/163 邮箱请填写授权码而非登录密码</div>
        </div>
      </div>
      <div class="setting-row-right">
        <el-input v-model="form.smtp_password" placeholder="邮箱授权码" type="password" show-password size="large" style="width:240px;" />
      </div>
    </div>

    <div class="setting-divider" />

    <!-- 使用 TLS -->
    <div class="setting-row">
      <div class="setting-row-left">
        <div class="setting-row-icon" style="background:rgba(0,122,255,0.1);color:#007aff;">
          <el-icon :size="22"><Switch /></el-icon>
        </div>
        <div class="setting-row-body">
          <div class="setting-row-title">使用 TLS</div>
          <div class="setting-row-desc">端口 587 请开启，465 请关闭</div>
        </div>
      </div>
      <div class="setting-row-right">
        <el-switch v-model="form.smtp_use_tls" />
      </div>
    </div>

    <div class="setting-divider" />

    <!-- 收件人邮箱 -->
    <div class="setting-row">
      <div class="setting-row-left">
        <div class="setting-row-icon" style="background:rgba(0,122,255,0.1);color:#007aff;">
          <el-icon :size="22"><Stamp /></el-icon>
        </div>
        <div class="setting-row-body">
          <div class="setting-row-title">收件人邮箱</div>
          <div class="setting-row-desc">接收用户反馈通知的邮箱地址</div>
        </div>
      </div>
      <div class="setting-row-right">
        <el-input v-model="form.feedback_recipient" placeholder="recipient@qq.com" size="large" style="width:240px;" />
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

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminGetSettings, adminUpdateSettings, getActiveModels } from '../../api'
import { adminListModels, adminCreateModel, adminUpdateModel, adminDeleteModel, adminToggleModel, adminTestModel, adminGetModelStats } from '../../api'

/* ========== 模型配置 ========== */
const models = ref([])
const modelStats = ref([])
const modelLoading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const editingId = ref(null)
const submitting = ref(false)
const modelForm = reactive({ provider: '', model_name: '', api_base: '', api_key: '' })

const providerPresets = [
  { label: '硅基流动', value: '硅基流动', apiBase: 'https://api.siliconflow.cn/v1' },
  { label: 'OpenAI', value: 'OpenAI', apiBase: 'https://api.openai.com/v1' },
  { label: 'DeepSeek', value: 'DeepSeek', apiBase: 'https://api.deepseek.com/v1' },
]

function onProviderChange(val) {
  const preset = providerPresets.find(p => p.value === val)
  if (preset) modelForm.api_base = preset.apiBase
}
function resetModelForm() { modelForm.provider=''; modelForm.model_name=''; modelForm.api_base=''; modelForm.api_key=''; editingId.value=null }
function openCreate() { resetModelForm(); dialogTitle.value='添加模型'; dialogVisible.value=true }
function openEdit(m) { editingId.value=m.id; dialogTitle.value='编辑模型'; modelForm.provider=m.provider; modelForm.model_name=m.model_name; modelForm.api_base=m.api_base; modelForm.api_key=''; dialogVisible.value=true }

async function handleModelSubmit() {
  if (!modelForm.provider || !modelForm.model_name || !modelForm.api_base || (!editingId.value && !modelForm.api_key)) {
    return ElMessage.warning('请填写完整信息')
  }
  submitting.value = true
  try {
    if (editingId.value) {
      const d = { provider:modelForm.provider, model_name:modelForm.model_name, api_base:modelForm.api_base }
      if (modelForm.api_key) d.api_key = modelForm.api_key
      await adminUpdateModel(editingId.value, d); ElMessage.success('已更新')
    } else {
      await adminCreateModel({ ...modelForm }); ElMessage.success('已添加')
    }
    dialogVisible.value=false; await loadModels()
  } catch {} finally { submitting.value=false }
}

async function handleDelete(m) {
  try { await ElMessageBox.confirm(`删除 ${m.provider} ${m.model_name}？`,'确认',{type:'warning'}); await adminDeleteModel(m.id); ElMessage.success('已删除'); await loadModels() }
  catch (e) { if (e!=='cancel') console.error(e) }
}

async function handleTest(m) {
  try {
    const r = await adminTestModel(m.id)
    if (r.data.ok) { ElMessage.success(r.data.message) }
    else { ElMessage.error(r.data.message) }
  } catch {}
}

async function handleToggle(m) {
  try { await adminToggleModel(m.id); ElMessage.success(m.is_active?'已禁用':'已启用'); await loadModels() }
  catch (e) { console.error(e) }
}

async function loadModels() {
  modelLoading.value=true
  try {
    const [mr, sr] = await Promise.all([adminListModels(), adminGetModelStats()])
    models.value = mr.data
    modelStats.value = sr.data
  } catch {} finally { modelLoading.value=false }
}

function getModelStat(id) {
  return modelStats.value.find(s => s.id === id)
}

/* ========== 系统设置 ========== */
const loading = ref(false)
const saving = ref(false)
const activeModels = ref([])

const form = reactive({
  max_chars: 100000,
  points_per_10000_chars: 1,
  active_model_id: '',
  deep_model_id: '',
  fast_model_id: '',
  score_timeout: 300,
  smtp_host: 'smtp.qq.com',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  smtp_use_tls: true,
  feedback_recipient: '',
})

onMounted(async () => {
  await loadModels()
  loading.value = true
  try {
    const [settingsRes, modelsRes] = await Promise.all([
      adminGetSettings(),
      getActiveModels(),
    ])
    activeModels.value = modelsRes.data
    for (const item of settingsRes.data) {
      const v = item.value
      const n = parseInt(v)
      if (item.key === 'max_chars') form.max_chars = isNaN(n) ? 100000 : n
      if (item.key === 'points_per_10000_chars') form.points_per_10000_chars = isNaN(n) ? 1 : n
      if (item.key === 'active_model_id') form.active_model_id = v || ''
      if (item.key === 'deep_model_id') form.deep_model_id = v || ''
      if (item.key === 'fast_model_id') form.fast_model_id = v || ''
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
      { key: 'deep_model_id', value: form.deep_model_id },
      { key: 'fast_model_id', value: form.fast_model_id },
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
  <div style="display:flex;flex-direction:column;gap:24px;">
    <!-- ========== 模型配置 ========== -->
    <div class="glass-card" style="padding:0;overflow:hidden;">
      <div style="padding:20px 28px 0;">
        <div style="font-size:15px;font-weight:600;">模型配置</div>
        <div style="font-size:13px;color:var(--text-secondary);margin-top:3px;">管理 AI 评分模型及 API Key</div>
      </div>
      <div class="table-toolbar">
        <span class="toolbar-count">共 {{ models.length }} 个模型</span>
        <el-button type="primary" @click="openCreate">+ 添加模型</el-button>
      </div>
      <div class="table-wrap">
        <el-table :data="models" v-loading="modelLoading" stripe>
          <el-table-column prop="id" label="ID" width="55" align="center" />
          <el-table-column label="厂商" width="100">
            <template #default="{row}"><el-tag effect="light" size="small">{{ row.provider }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="model_name" label="模型名" min-width="140" />
          <el-table-column prop="api_base" label="API 地址" min-width="220">
            <template #default="{row}"><code style="font-size:12px;word-break:break-all;">{{ row.api_base }}</code></template>
          </el-table-column>
          <el-table-column label="API Key" width="155">
            <template #default="{row}"><code style="font-size:12px;">{{ row.api_key_masked }}</code></template>
          </el-table-column>
          <el-table-column label="状态" width="70" align="center">
            <template #default="{row}"><span class="dot" :class="row.is_active?'on':'off'" />{{ row.is_active?'启用':'禁用' }}</template>
          </el-table-column>
          <el-table-column label="评分次数" width="90" align="center">
            <template #default="{row}">{{ getModelStat(row.id)?.score_count || 0 }}</template>
          </el-table-column>
          <el-table-column label="平均耗时" width="100" align="center">
            <template #default="{row}">
              <span v-if="getModelStat(row.id)?.avg_elapsed" style="font-weight:600;color:var(--accent)">{{ getModelStat(row.id).avg_elapsed }}s</span>
              <span v-else style="color:var(--text-tertiary)">-</span>
            </template>
          </el-table-column>
          <el-table-column label="最快" width="80" align="center">
            <template #default="{row}">
              <span v-if="getModelStat(row.id)?.min_elapsed" style="color:var(--green)">{{ getModelStat(row.id).min_elapsed }}s</span>
              <span v-else style="color:var(--text-tertiary)">-</span>
            </template>
          </el-table-column>
          <el-table-column label="最慢" width="80" align="center">
            <template #default="{row}">
              <span v-if="getModelStat(row.id)?.max_elapsed" style="color:var(--red)">{{ getModelStat(row.id).max_elapsed }}s</span>
              <span v-else style="color:var(--text-tertiary)">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="280" fixed="right" align="center">
            <template #default="{row}">
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" @click="handleTest(row)">测试</el-button>
              <el-button size="small" :type="row.is_active?'warning':'success'" @click="handleToggle(row)">{{ row.is_active?'禁用':'启用' }}</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-if="!modelLoading && models.length===0" class="empty-state">
        <div class="empty-icon"><el-icon :size="36"><Setting /></el-icon></div>
        <p>暂无模型配置，请添加</p>
      </div>
    </div>

    <!-- 模型弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px" align-center :close-on-click-modal="false">
      <div class="dialog-form">
        <el-select v-model="modelForm.provider" placeholder="选择厂商" size="large" filterable allow-create @change="onProviderChange">
          <el-option v-for="p in providerPresets" :key="p.value" :label="p.label" :value="p.value" />
        </el-select>
        <el-input v-model="modelForm.model_name" placeholder="模型名（gpt-4o / deepseek-chat / Qwen/Qwen3-235B-A22B）" size="large" />
        <el-input v-model="modelForm.api_base" placeholder="API 地址" size="large" />
        <el-input v-model="modelForm.api_key" :placeholder="editingId?'留空不修改密钥':'API Key'" size="large" show-password />
      </div>
      <template #footer>
        <el-button @click="dialogVisible=false" :disabled="submitting" size="large">取消</el-button>
        <el-button type="primary" @click="handleModelSubmit" :loading="submitting" size="large">保存</el-button>
      </template>
    </el-dialog>

    <!-- ========== 系统设置 ========== -->
    <div class="glass-card" style="padding:0;" v-loading="loading">
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

      <!-- 深度评分模型 -->
      <div class="setting-row">
        <div class="setting-row-left">
          <div class="setting-row-icon" style="background:rgba(88,86,214,0.1);color:#5856d6;">
            <el-icon :size="22"><Cpu /></el-icon>
          </div>
          <div class="setting-row-body">
            <div class="setting-row-title">深度评分模型</div>
            <div class="setting-row-desc">用户点击「深度评分」时使用的 AI 模型</div>
          </div>
        </div>
        <div class="setting-row-right">
          <el-select v-model="form.deep_model_id" placeholder="选择模型" style="width:260px;" size="large">
            <el-option v-for="m in activeModels" :key="m.id" :label="`${m.provider} / ${m.model_name}`" :value="String(m.id)" />
          </el-select>
        </div>
      </div>

      <div class="setting-divider" />

      <!-- 快速评分模型 -->
      <div class="setting-row">
        <div class="setting-row-left">
          <div class="setting-row-icon" style="background:rgba(52,199,89,0.1);color:#34c759;">
            <el-icon :size="22"><Cpu /></el-icon>
          </div>
          <div class="setting-row-body">
            <div class="setting-row-title">快速评分模型</div>
            <div class="setting-row-desc">用户点击「快速评分」时使用的 AI 模型</div>
          </div>
        </div>
        <div class="setting-row-right">
          <el-select v-model="form.fast_model_id" placeholder="选择模型" style="width:260px;" size="large">
            <el-option v-for="m in activeModels" :key="m.id" :label="`${m.provider} / ${m.model_name}`" :value="String(m.id)" />
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
  </div>
</template>

<style scoped>
/* 模型配置 */
.table-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; gap: 12px; border-bottom:1px solid rgba(0,0,0,0.04); }
.toolbar-count { font-size:13px; color:var(--text-secondary); }
.table-wrap { overflow-x: auto; }
.dot { display:inline-block; width:6px; height:6px; border-radius:50%; margin-right:5px; vertical-align:middle; }
.dot.on { background:var(--green); } .dot.off { background:var(--red); }
.dialog-form { display:flex; flex-direction:column; gap:14px; }
.empty-state { text-align:center; padding:40px; color:var(--text-tertiary); }

/* 系统设置 */
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
.setting-footer { position: sticky; bottom: 0; z-index: 10; padding: 16px 28px; background: rgba(255,255,255,0.85); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); border-top: 1px solid rgba(0,0,0,0.05); display: flex; }

@media (max-width: 640px) {
  .setting-row { flex-direction: column; align-items: flex-start; }
  .setting-row-right { padding-left: 60px; }
}
</style>

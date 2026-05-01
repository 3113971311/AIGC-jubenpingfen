<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminListModels, adminCreateModel, adminUpdateModel, adminDeleteModel, adminToggleModel, adminTestModel } from '../../api'

const models = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const editingId = ref(null)
const submitting = ref(false)
const form = reactive({ provider: '', model_name: '', api_base: '', api_key: '' })

// 快捷厂商预设
const providerPresets = [
  { label: '硅基流动', value: '硅基流动', apiBase: 'https://api.siliconflow.cn/v1' },
  { label: 'OpenAI', value: 'OpenAI', apiBase: 'https://api.openai.com/v1' },
  { label: 'DeepSeek', value: 'DeepSeek', apiBase: 'https://api.deepseek.com/v1' },
]

function onProviderChange(val) {
  const preset = providerPresets.find(p => p.value === val)
  if (preset) form.api_base = preset.apiBase
}

function reset() { form.provider=''; form.model_name=''; form.api_base=''; form.api_key=''; editingId.value=null }
function openCreate() { reset(); dialogTitle.value='添加模型'; dialogVisible.value=true }
function openEdit(m) { editingId.value=m.id; dialogTitle.value='编辑模型'; form.provider=m.provider; form.model_name=m.model_name; form.api_base=m.api_base; form.api_key=''; dialogVisible.value=true }

async function handleSubmit() {
  if (!form.provider || !form.model_name || !form.api_base || (!editingId.value && !form.api_key)) {
    return ElMessage.warning('请填写完整信息')
  }
  submitting.value = true
  try {
    if (editingId.value) {
      const d = { provider:form.provider, model_name:form.model_name, api_base:form.api_base }
      if (form.api_key) d.api_key = form.api_key
      await adminUpdateModel(editingId.value, d); ElMessage.success('已更新')
    } else {
      await adminCreateModel({ ...form }); ElMessage.success('已添加')
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
  loading.value=true
  try { const r=await adminListModels(); models.value=r.data } catch {} finally { loading.value=false }
}
onMounted(loadModels)
</script>

<template>
  <div class="glass-panel admin-page-panel">
    <div class="table-toolbar">
      <span class="toolbar-count">共 {{ models.length }} 个模型</span>
      <el-button type="primary" @click="openCreate">+ 添加模型</el-button>
    </div>
    <div class="table-wrap">
      <el-table :data="models" v-loading="loading" stripe>
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
    <div v-if="!loading && models.length===0" class="empty-state">
      <div class="empty-icon"><el-icon :size="36"><Setting /></el-icon></div>
      <p>暂无模型配置，请添加</p>
    </div>
  </div>

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px" align-center :close-on-click-modal="false">
    <div class="dialog-form">
      <el-select v-model="form.provider" placeholder="选择厂商" size="large" filterable allow-create @change="onProviderChange">
        <el-option v-for="p in providerPresets" :key="p.value" :label="p.label" :value="p.value" />
      </el-select>
      <el-input v-model="form.model_name" placeholder="模型名（gpt-4o / deepseek-chat / Qwen/Qwen3-235B-A22B）" size="large" />
      <el-input v-model="form.api_base" placeholder="API 地址" size="large" />
      <el-input v-model="form.api_key" :placeholder="editingId?'留空不修改密钥':'API Key'" size="large" show-password />
    </div>
    <template #footer>
      <el-button @click="dialogVisible=false" :disabled="submitting" size="large">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting" size="large">保存</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.admin-page-panel { overflow: hidden; }
.table-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; gap: 12px; border-bottom:1px solid rgba(0,0,0,0.04); }
.toolbar-count { font-size:13px; color:var(--text-secondary); }
.table-wrap { overflow-x: auto; }
.dot { display:inline-block; width:6px; height:6px; border-radius:50%; margin-right:5px; vertical-align:middle; }
.dot.on { background:var(--green); } .dot.off { background:var(--red); }
.dialog-form { display:flex; flex-direction:column; gap:14px; }
</style>

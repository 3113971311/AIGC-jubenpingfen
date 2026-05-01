<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminListUsers, adminCreateUser, adminUpdateUser, adminDeleteUser, adminToggleUser } from '../../api'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()

const users = ref([])
const loading = ref(false)
const search = ref('')
const dialogVisible = ref(false)
const dialogTitle = ref('')
const editingId = ref(null)
const submitting = ref(false)
const originalPoints = ref(0)

const form = reactive({ username: '', password: '', points: 0, is_admin: false })
const quickPoints = [0, 5, 10, 20, 50, 100]
const rechargeAmounts = [5, 10, 20, 50, 100, 200]

function quickSet(v) { form.points = v }
function quickAdd(v) { form.points += v }

function resetForm() { form.username = ''; form.password = ''; form.points = 0; form.is_admin = false; editingId.value = null; originalPoints.value = 0 }
function openCreate() { resetForm(); dialogTitle.value = '创建用户'; dialogVisible.value = true }
function openEdit(u) { editingId.value = u.id; dialogTitle.value = '编辑 — ' + u.username; form.username = u.username; form.password = ''; form.points = u.points; form.is_admin = u.is_admin; originalPoints.value = u.points; dialogVisible.value = true }

async function handleSubmit() {
  if (!form.username || form.username.length < 2) return ElMessage.warning('用户名至少2个字符')
  if (!editingId.value && (!form.password || form.password.length < 4)) return ElMessage.warning('密码至少4位')
  if (editingId.value && form.password && form.password.length < 4) return ElMessage.warning('密码至少4位')
  submitting.value = true
  try {
    if (editingId.value) {
      const d = { username: form.username, points: form.points, is_admin: form.is_admin }
      if (form.password) d.password = form.password
      await adminUpdateUser(editingId.value, d); ElMessage.success('已更新')
      auth.refreshUser()
    } else {
      await adminCreateUser({ username: form.username, password: form.password, points: form.points, is_admin: form.is_admin })
      ElMessage.success('已创建')
    }
    dialogVisible.value = false; await loadUsers()
  } catch {} finally { submitting.value = false }
}

async function handleToggle(u) {
  const a = u.is_active ? '禁用' : '启用'
  try { await ElMessageBox.confirm(`确定${a}用户 ${u.username}？`); await adminToggleUser(u.id); ElMessage.success(`已${a}`); await loadUsers() }
  catch (e) { if (e !== 'cancel') console.error(e) }
}

async function handleDelete(u) {
  if (u.is_admin) return ElMessage.warning('不能删除管理员')
  try { await ElMessageBox.confirm(`永久删除 ${u.username}？不可恢复！`, '危险操作', { type: 'error', confirmButtonText: '永久删除' }); await adminDeleteUser(u.id); ElMessage.success('已删除'); await loadUsers() }
  catch (e) { if (e !== 'cancel') console.error(e) }
}

async function loadUsers() {
  loading.value = true
  try { const r = await adminListUsers({ search: search.value, page_size: 100 }); users.value = r.data } catch {} finally { loading.value = false }
}

onMounted(loadUsers)

function fmtDate(d) {
  if (!d) return ''
  const s = String(d)
  const date = s.endsWith('Z') || s.includes('+') ? new Date(s) : new Date(s + 'Z')
  return date.toLocaleString('zh-CN')
}
</script>

<template>
  <div class="glass-panel admin-page-panel">
    <div class="table-toolbar">
      <div class="toolbar-left">
        <el-input v-model="search" placeholder="搜索用户名..." :prefix-icon="Search" clearable @input="loadUsers" style="width:240px;" />
      </div>
      <el-button type="primary" @click="openCreate">+ 创建用户</el-button>
    </div>

    <div class="table-wrap">
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="55" align="center" />
        <el-table-column prop="username" label="用户名" min-width="110" />
        <el-table-column label="积分" width="90" align="center">
          <template #default="{row}"><span class="pts">{{ row.points }}</span></template>
        </el-table-column>
        <el-table-column label="角色" width="80" align="center">
          <template #default="{row}"><el-tag :type="row.is_admin?'danger':'info'" size="small" effect="light">{{ row.is_admin?'管理员':'用户' }}</el-tag></template>
        </el-table-column>
        <el-table-column label="状态" width="70" align="center">
          <template #default="{row}"><span class="dot" :class="row.is_active?'on':'off'" />{{ row.is_active?'正常':'禁用' }}</template>
        </el-table-column>
        <el-table-column label="创建时间" width="155">
          <template #default="{row}"><span class="time-cell">{{ fmtDate(row.created_at) }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{row}">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" :type="row.is_active?'warning':'success'" @click="handleToggle(row)">{{ row.is_active?'禁用':'启用' }}</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div v-if="!loading && users.length===0" class="empty-state">
      <div class="empty-icon"><el-icon :size="36"><User /></el-icon></div>
      <p>{{ search ? '未找到匹配用户' : '暂无用户' }}</p>
    </div>
  </div>

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px" align-center :close-on-click-modal="false">
    <div class="dialog-form">
      <el-input v-model="form.username" placeholder="用户名" size="large" />
      <el-input v-model="form.password" type="password" :placeholder="editingId?'留空不修改密码':'密码（至少4位）'" size="large" show-password />
      <div class="form-section">
        <div class="section-top">
          <span class="section-label">积分设置</span>
          <span v-if="editingId" class="section-diff">
            当前 {{ originalPoints }}
            <span v-if="form.points>originalPoints" class="green">+{{ form.points-originalPoints }}</span>
            <span v-else-if="form.points<originalPoints" class="red">-{{ originalPoints-form.points }}</span>
            <span v-else>不变</span>
          </span>
        </div>
        <el-input-number v-model="form.points" :min="0" :controls="false" size="large" style="width:100%;" />
        <div class="chip-row">
          <button v-for="v in quickPoints" :key="'s'+v" class="chip" :class="{on:form.points===v}" @click="quickSet(v)">{{ v }}</button>
        </div>
      </div>
      <div v-if="editingId" class="form-section">
        <span class="section-label">快捷充值</span>
        <div class="chip-row">
          <button v-for="v in rechargeAmounts" :key="'r'+v" class="chip plus" @click="quickAdd(v)">+{{ v }}</button>
        </div>
      </div>
      <el-checkbox v-model="form.is_admin" label="管理员权限" />
    </div>
    <template #footer>
      <el-button @click="dialogVisible=false" :disabled="submitting" size="large">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting" size="large">保存</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.admin-page-panel { overflow: hidden; }
.table-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; gap: 12px; flex-wrap: wrap; border-bottom:1px solid rgba(0,0,0,0.04); }
.toolbar-left { display: flex; gap: 12px; align-items: center; }
.table-wrap { overflow-x: auto; }
.pts { font-weight:700; color:var(--accent); background:rgba(0,122,255,0.08); padding:2px 10px; border-radius:10px; font-size:13px; }
.dot { display:inline-block; width:6px; height:6px; border-radius:50%; margin-right:5px; vertical-align:middle; }
.dot.on { background:var(--green); } .dot.off { background:var(--red); }
.time-cell { font-size:13px; white-space:nowrap; }

.dialog-form { display:flex; flex-direction:column; gap:14px; }
.form-section { background:rgba(0,0,0,0.02); border-radius:14px; padding:14px; }
.section-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.section-label { font-size:13px; color:var(--text-secondary); font-weight:500; }
.section-diff { font-size:12px; color:var(--text-tertiary); }
.green { color:var(--green); font-weight:600; } .red { color:var(--red); font-weight:600; }

.chip-row { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
.chip { padding:5px 14px; border-radius:20px; border:1px solid rgba(0,0,0,0.1); background:rgba(255,255,255,0.6); font-size:13px; font-family:inherit; color:var(--text-secondary); cursor:pointer; transition:all .2s; }
.chip:hover { border-color:var(--accent); color:var(--accent); background:rgba(0,122,255,0.06); }
.chip.on { background:var(--accent); border-color:var(--accent); color:#fff; font-weight:600; }
.chip.plus { color:var(--green); border-color:rgba(52,199,89,0.3); }
.chip.plus:hover { background:rgba(52,199,89,0.08); border-color:var(--green); }

@media (max-width:768px) {
  .table-toolbar { flex-direction:column; align-items:stretch; }
  .toolbar-left .el-input { width:100% !important; }
  .section-top { flex-direction:column; align-items:flex-start; gap:4px; }
}
</style>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listScripts, uploadScript, createTextScript, scoreScript, deleteScript, getScoreHistory, getScoreProgress, submitFeedback } from '../api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const scripts = ref([])
const uploading = ref(false)
const pasting = ref(false)
const scoringId = ref(null)
const scoredIds = ref(new Set())

const textForm = reactive({ title: '', content: '' })

// 评分进度状态
const progressState = reactive({
  visible: false,
  scriptTitle: '',
  scoreId: null,
  progress: '正在准备...',
  elapsed: 0,
})
let progressTimer = null
let pollTimer = null

// 自动识别标题
function extractTitle(text) {
  if (!text) return ''
  let title = ''
  const bracket = text.match(/《(.+?)》/)
  if (bracket) {
    title = `《${bracket[1]}》`
  } else {
    const label = text.match(/(?:剧名|剧本名|标题|片名)[：:]\s*(.+)/)
    if (label) title = label[1].split(/[\n\r]/)[0].slice(0, 50).trim()
    else {
      const hash = text.match(/^#\s+(.+)/m)
      if (hash) title = hash[1].slice(0, 50).trim()
    }
  }
  const episodes = [...text.matchAll(/第(\d+)\s*集/g)].map(m => parseInt(m[1]))
  const scenes = [...text.matchAll(/第(\d+)\s*场/g)].map(m => parseInt(m[1]))
  const parts = []
  if (episodes.length) {
    const min = Math.min(...episodes), max = Math.max(...episodes)
    parts.push(min === max ? `第${min}集` : `第${min}-${max}集`)
  }
  if (scenes.length) {
    const min = Math.min(...scenes), max = Math.max(...scenes)
    parts.push(min === max ? `第${min}场` : `第${min}-${max}场`)
  }
  if (parts.length) title = title ? `${title} ${parts.join(' ')}` : parts.join(' ')
  return title
}

let lastAutoTitle = ''
watch(() => textForm.content, (val) => {
  if (!textForm.title || textForm.title === lastAutoTitle) {
    const t = extractTitle(val)
    if (t) { textForm.title = t; lastAutoTitle = t }
  }
})

const STORAGE_KEY = 'scoring_in_progress'
const storageScoring = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '[]')
const scoringSet = ref(new Set(storageScoring))

async function loadScripts() {
  try { const r = await listScripts({ page: 1, page_size: 50 }); scripts.value = r.data } catch {}
}
async function loadScores() {
  try {
    const r = await getScoreHistory({ page_size: 200 })
    const allScoreIds = new Set(r.data.map(s => s.script_id))
    const completedIds = new Set(r.data.filter(s => s.overall > 0).map(s => s.script_id))
    for (const id of scoringSet.value) {
      if (completedIds.has(id)) scoringSet.value.delete(id)
      else if (!allScoreIds.has(id)) scoringSet.value.delete(id)
    }
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...scoringSet.value]))
    scoredIds.value = new Set([...completedIds, ...scoringSet.value])
  } catch {}
}

onMounted(() => { loadScripts(); loadScores(); auth.refreshUser() })

function stopPolling() {
  if (progressTimer) { clearInterval(progressTimer); progressTimer = null }
  if (pollTimer) { clearTimeout(pollTimer); pollTimer = null }
}

onUnmounted(() => { stopPolling() })

async function handleScore(scriptId) {
  const script = scripts.value.find(s => s.id === scriptId)
  const title = script?.title || '剧本'

  scoringId.value = scriptId
  scoringSet.value.add(scriptId)
  scoredIds.value.add(scriptId)
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...scoringSet.value]))

  try {
    const r = await scoreScript(scriptId, 0)
    const scoreId = r.data.id

    progressState.visible = true
    progressState.scriptTitle = title
    progressState.scoreId = scoreId
    progressState.progress = r.data.progress || '正在准备...'
    progressState.elapsed = 0

    progressTimer = setInterval(() => { progressState.elapsed++ }, 1000)

    const POLL_INTERVAL = 2000
    const MAX_WAIT = 600000 // 10 分钟安全上限

    const poll = async () => {
      try {
        const pr = await getScoreProgress(scoreId)
        progressState.progress = pr.data.progress || '处理中...'

        if (pr.data.overall > 0) {
          stopPolling()
          progressState.visible = false
          scoringSet.value.delete(scriptId)
          sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...scoringSet.value]))
          scoredIds.value.add(scriptId)
          await auth.refreshUser()
          ElMessage.success('评分完成')
          router.push(`/score/${scoreId}`)
          return
        }
        pollTimer = setTimeout(poll, POLL_INTERVAL)
      } catch {
        if (progressState.visible) pollTimer = setTimeout(poll, POLL_INTERVAL)
      }
    }

    // 给后端 1 秒缓冲时间再开始轮询
    pollTimer = setTimeout(poll, 1000)
  } catch (e) {
    scoringSet.value.delete(scriptId)
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...scoringSet.value]))
  } finally {
    scoringId.value = null
  }
}

function cancelScore() {
  stopPolling()
  progressState.visible = false
  loadScores()
}

async function handleUpload(file) {
  uploading.value = true
  try { await uploadScript(file); ElMessage.success('上传成功'); await loadScripts() }
  catch {} finally { uploading.value = false }
}

function handleFileChange(e) {
  const f = e.target.files?.[0]; if (!f) return; handleUpload(f); e.target.value = ''
}

async function handlePaste() {
  if (!textForm.content.trim()) return ElMessage.warning('请输入剧本内容')
  pasting.value = true
  try {
    await createTextScript(textForm.title.trim() || '未命名剧本', textForm.content)
    ElMessage.success('提交成功')
    textForm.title = ''; textForm.content = ''
    await loadScripts()
  } catch {} finally { pasting.value = false }
}

async function handleDelete(scriptId) {
  try {
    await ElMessageBox.confirm('确定删除该剧本？', '确认', { type: 'warning' })
    await deleteScript(scriptId)
    ElMessage.success('已删除')
    await loadScripts()
  } catch (e) { if (e !== 'cancel') console.error(e) }
}

function fmtDate(d) {
  if (!d) return ''
  const s = String(d)
  const date = s.endsWith('Z') || s.includes('+') ? new Date(s) : new Date(s + 'Z')
  return date.toLocaleString('zh-CN')
}

// 反馈弹窗
const feedbackVisible = ref(false)
const feedbackForm = reactive({ contact: '', content: '' })
const feedbackSending = ref(false)

async function handleFeedback() {
  if (!feedbackForm.content.trim()) return ElMessage.warning('请输入反馈内容')
  feedbackSending.value = true
  try {
    const r = await submitFeedback({ contact: feedbackForm.contact.trim(), content: feedbackForm.content.trim() })
    if (r.data.ok) {
      ElMessage.success(r.data.message || '反馈已发送')
      feedbackVisible.value = false
      feedbackForm.contact = ''
      feedbackForm.content = ''
    } else {
      ElMessage.error(r.data.message || '发送失败')
    }
  } catch {} finally {
    feedbackSending.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <div class="upload-row">
      <div class="upload-card glass-card">
        <div class="upload-icon"><el-icon :size="32"><UploadFilled /></el-icon></div>
        <h3>上传文件</h3>
        <p class="upload-desc">支持 txt / docx / pdf</p>
        <label class="upload-btn glass-btn glass-btn-primary">
          <el-icon :size="18"><Upload /></el-icon>
          {{ uploading ? '上传中...' : '选择文件' }}
          <input type="file" accept=".txt,.docx,.pdf" @change="handleFileChange" hidden :disabled="uploading" />
        </label>
      </div>

      <div class="upload-card glass-card">
        <div class="upload-icon" style="color:var(--accent);"><el-icon :size="32"><EditPen /></el-icon></div>
        <h3>粘贴文本</h3>
        <p class="upload-desc">直接输入或粘贴剧本文字</p>
        <div class="text-form">
          <el-input v-model="textForm.title" placeholder="剧本名称（可选）" size="default" maxlength="200" clearable />
          <el-input v-model="textForm.content" type="textarea" placeholder="在此粘贴或输入剧本内容..." :rows="4" resize="vertical" />
          <el-button type="primary" :loading="pasting" @click="handlePaste">{{ pasting ? '提交中...' : '提交剧本' }}</el-button>
        </div>
      </div>
    </div>

    <h2 class="page-title" style="margin-bottom:20px;">我的剧本</h2>
    <div v-if="scripts.length === 0" class="empty-state glass-card">
      <div class="empty-icon"><el-icon :size="40"><FolderOpened /></el-icon></div>
      <p>还没有上传剧本</p>
    </div>
    <div v-else class="glass-grid">
      <div v-for="s in scripts" :key="s.id" class="script-card glass-card">
        <h3>{{ s.title }}</h3>
        <div class="script-meta">
          <span>字数: {{ s.char_count.toLocaleString() }}</span>
          <span>{{ fmtDate(s.created_at) }}</span>
        </div>
        <div class="script-actions">
          <el-button v-if="scoringSet.has(s.id)" type="warning" size="small" disabled>评分中...</el-button>
          <el-button v-else-if="scoredIds.has(s.id)" type="success" size="small" disabled>已评分</el-button>
          <el-button v-else type="primary" size="small" :loading="scoringId === s.id" @click="handleScore(s.id)">AI 评分</el-button>
          <el-button size="small" @click="router.push(`/score/${s.id}`)">查看</el-button>
          <el-button size="small" type="danger" @click="handleDelete(s.id)">删除</el-button>
        </div>
      </div>
    </div>
  </div>

  <!-- 评分进度遮罩 -->
  <teleport to="body">
    <div v-if="progressState.visible" class="progress-overlay">
      <div class="progress-dialog glass-card">
        <div class="progress-header">
          <el-icon :size="24" class="progress-spin"><Loading /></el-icon>
          <h3>AI 正在评分...</h3>
        </div>
        <p class="progress-script">{{ progressState.scriptTitle }}</p>
        <div class="progress-bar-track"><div class="progress-bar-fill" /></div>
        <p class="progress-text">{{ progressState.progress }}</p>
        <p class="progress-elapsed">已等待 {{ progressState.elapsed }} 秒</p>
        <el-button size="small" @click="cancelScore">后台运行</el-button>
      </div>
    </div>
  </teleport>

  <!-- 反馈悬浮气泡 -->
  <teleport to="body">
    <div class="feedback-bubble" @click="feedbackVisible = true" title="问题反馈">
      <el-icon :size="22"><ChatDotSquare /></el-icon>
    </div>
  </teleport>

  <!-- 反馈弹窗 -->
  <el-dialog v-model="feedbackVisible" title="问题反馈" width="460px" :close-on-click-modal="false" destroy-on-close>
    <div class="feedback-body">
      <p class="feedback-tip">欢迎提出宝贵意见，我们会尽快回复。</p>
      <el-input v-model="feedbackForm.contact" placeholder="联系方式（邮箱/微信，选填）" maxlength="200" clearable />
      <el-input v-model="feedbackForm.content" type="textarea" placeholder="请描述您的问题或建议..." :rows="5" resize="vertical" maxlength="5000" show-word-limit />
    </div>
    <template #footer>
      <el-button @click="feedbackVisible = false">取消</el-button>
      <el-button type="primary" :loading="feedbackSending" @click="handleFeedback">发送反馈</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.upload-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
.upload-card { padding: 32px 24px; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.upload-icon { margin-bottom: 10px; display: flex; justify-content: center; color: var(--text-secondary); }
.upload-card h3 { font-size: 18px; font-weight: 600; margin-bottom: 4px; }
.upload-desc { color: var(--text-secondary); font-size: 13px; margin-bottom: 18px; }
.upload-btn { display: inline-flex; align-items: center; gap: 8px; padding: 10px 28px; font-size: 15px; cursor: pointer; }
.text-form { width: 100%; display: flex; flex-direction: column; gap: 10px; }
.script-card { padding: 22px; }
.script-card h3 { font-size: 17px; font-weight: 600; margin-bottom: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.script-meta { display: flex; gap: 16px; font-size: 13px; color: var(--text-secondary); margin-bottom: 14px; }
.script-actions { display: flex; gap: 8px; flex-wrap: wrap; }

.progress-overlay { position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; }
.progress-dialog { width: 400px; max-width: 90vw; padding: 32px 28px; text-align: center; }
.progress-header { display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 8px; }
.progress-spin { animation: spin 1.5s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.progress-script { font-size: 14px; color: var(--text-secondary); margin-bottom: 12px; }
.progress-bar-track { height: 4px; background: rgba(0,0,0,0.06); border-radius: 2px; overflow: hidden; margin-bottom: 12px; }
.progress-bar-fill { height: 100%; width: 30%; background: linear-gradient(90deg, var(--accent, #007aff), var(--primary, #5856d6)); border-radius: 2px; animation: progress-slide 1.8s ease-in-out infinite; }
@keyframes progress-slide { 0% { transform: translateX(-100%); } 100% { transform: translateX(430%); } }
.progress-text { font-size: 14px; color: var(--text-primary); margin-bottom: 6px; }
.progress-elapsed { font-size: 12px; color: var(--text-tertiary); }

.feedback-bubble {
  position: fixed; bottom: 28px; right: 28px; z-index: 9990;
  width: 52px; height: 52px;
  border-radius: 50%;
  background: var(--glass-bg);
  backdrop-filter: blur(var(--blur));
  -webkit-backdrop-filter: blur(var(--blur));
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow-lg);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  color: var(--accent);
  transition: all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
  user-select: none;
}
.feedback-bubble:hover {
  transform: scale(1.1);
  box-shadow: 0 12px 40px rgba(0, 122, 255, 0.18);
  background: var(--glass-bg-hover);
}
.feedback-body {
  display: flex; flex-direction: column; gap: 14px;
}
.feedback-tip {
  font-size: 14px; color: var(--text-secondary); margin: 0;
}

@media (max-width: 640px) { .upload-row { grid-template-columns: 1fr; } .script-meta { flex-direction: column; gap: 4px; } }
</style>

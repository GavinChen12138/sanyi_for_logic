<script setup>
/**
 * SuperView.vue — 高校数据管理页面（仅 super_admin）
 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getVersions, uploadSchools, rollbackVersion, getSchoolsList, getGroupDetail, editGroup } from '@/api/super'
import { GRADE_OPTIONS } from '@/constants'

const activeTab = ref('versions')

// ── 版本管理 ──
const versions = ref([])
const versionsLoading = ref(false)

async function fetchVersions() {
  versionsLoading.value = true
  try {
    versions.value = await getVersions()
  } catch (err) {
    ElMessage.error(err.message || '获取版本列表失败')
  } finally {
    versionsLoading.value = false
  }
}

// 上传
const uploadDialogVisible = ref(false)
const uploadNote = ref('')
const uploadFileList = ref([])
const uploading = ref(false)

async function handleUpload() {
  if (!uploadFileList.value.length) {
    ElMessage.warning('请选择 JSON 文件')
    return
  }
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadFileList.value[0].raw)
    formData.append('note', uploadNote.value)
    const result = await uploadSchools(formData)
    ElMessage.success('上传成功')
    uploadDialogVisible.value = false
    uploadNote.value = ''
    uploadFileList.value = []
    await fetchVersions()
  } catch (err) {
    ElMessage.error(err.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

function handleFileChange(file) {
  // 校验文件类型
  if (!file.name.endsWith('.json')) {
    ElMessage.error('只接受 JSON 文件')
    return false
  }
  uploadFileList.value = [file]
  return false // 阻止自动上传
}

// 回滚
async function handleRollback(version) {
  try {
    await ElMessageBox.confirm(`确定回滚到 v${version.version_no}（${version.note || '无备注'}）吗？`, '确认回滚', { type: 'warning' })
    await rollbackVersion(version.id)
    ElMessage.success(`已回滚到 v${version.version_no}`)
    await fetchVersions()
  } catch { /* 用户取消 */ }
}

// 下载
function handleDownload(version) {
  const token = localStorage.getItem('token')
  const url = `/api/super/schools/versions/${version.id}/download`
  // 创建带鉴权的下载链接
  const a = document.createElement('a')
  fetch(url, { headers: { Authorization: `Bearer ${token}` } })
    .then(res => res.blob())
    .then(blob => {
      a.href = URL.createObjectURL(blob)
      a.download = `v${version.version_no}_schools.json`
      a.click()
      URL.revokeObjectURL(a.href)
    })
}

// ── 逐条编辑 ──
const schools = ref([])
const schoolsLoading = ref(false)
const searchKey = ref('')

async function fetchSchools() {
  schoolsLoading.value = true
  try {
    schools.value = await getSchoolsList()
  } catch (err) {
    ElMessage.error(err.message || '获取学校列表失败')
  } finally {
    schoolsLoading.value = false
  }
}

// 过滤学校
const filteredSchools = ref([])

function filterSchools() {
  if (!searchKey.value) {
    filteredSchools.value = schools.value
  } else {
    const key = searchKey.value.toLowerCase()
    filteredSchools.value = schools.value.filter(s =>
      s.name.toLowerCase().includes(key) ||
      (s.tags || []).some(t => t.toLowerCase().includes(key))
    )
  }
}

// 编辑弹窗
const editDialogVisible = ref(false)
const editingGroup = ref(null)
const editingSchoolName = ref('')
const editForm = reactive({
  preliminary_line: null,
  entry_rule_score: null,
  entry_rule_text: '',
  rules: { A: 0, B: 0, C: 0, D: 0, E: 0 },
  required_subjects: [],
  required_subjects_mode: 'or',
  last_year_composite_score: null,
  admission_count: null,
  description: ''
})

async function openEditDialog(schoolId, groupId) {
  try {
    const data = await getGroupDetail(schoolId, groupId)
    editingGroup.value = data
    editingSchoolName.value = data.school_name
    const g = data.group
    Object.assign(editForm, {
      preliminary_line: g.preliminary_line || 0,
      entry_rule_score: g.entry_rule?.score,
      entry_rule_text: g.entry_rule_text || '',
      rules: { ...g.rules },
      required_subjects: [...(g.required_subjects || [])],
      required_subjects_mode: g.required_subjects_mode || 'or',
      last_year_composite_score: g.last_year_composite_score || 0,
      admission_count: g.admission_count || 0,
      description: g.description || ''
    })
    editDialogVisible.value = true
  } catch (err) {
    ElMessage.error(err.message || '获取详情失败')
  }
}

async function handleSaveEdit() {
  try {
    const schoolId = editingGroup.value.school_id
    const groupId = editingGroup.value.group.id
    await editGroup(schoolId, groupId, editForm)
    ElMessage.success('编辑保存成功，已生成新版本')
    editDialogVisible.value = false
    await fetchSchools()
    await fetchVersions()
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  }
}

onMounted(async () => {
  await fetchVersions()
  await fetchSchools()
  filterSchools()
})
</script>

<template>
  <div class="page-container">
    <el-tabs v-model="activeTab">
      <!-- 版本管理 -->
      <el-tab-pane label="📦 版本管理" name="versions">
        <div class="tab-header">
          <el-button type="primary" @click="uploadDialogVisible = true" :icon="'Upload'">
            上传新版本
          </el-button>
        </div>
        <el-table :data="versions" v-loading="versionsLoading" stripe style="width: 100%">
          <el-table-column label="版本" width="80">
            <template #default="{ row }">v{{ row.version_no }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small" effect="dark">
                {{ row.is_active ? '当前使用' : '历史' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="school_count" label="院校数" width="80" align="center" />
          <el-table-column prop="group_count" label="专业组数" width="90" align="center" />
          <el-table-column prop="note" label="备注" min-width="200" show-overflow-tooltip />
          <el-table-column prop="uploaded_by_name" label="操作人" width="100" />
          <el-table-column label="上传时间" min-width="160">
            <template #default="{ row }">
              {{ row.uploaded_at ? new Date(row.uploaded_at).toLocaleString('zh-CN') : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click="handleDownload(row)">下载</el-button>
              <el-button text type="warning" size="small" :disabled="row.is_active" @click="handleRollback(row)">
                回滚
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 逐条编辑 -->
      <el-tab-pane label="✏️ 逐条编辑" name="edit">
        <div class="tab-header">
          <el-input
            v-model="searchKey"
            placeholder="搜索院校名称或标签..."
            clearable
            style="max-width: 320px"
            @input="filterSchools"
            :prefix-icon="'Search'"
          />
        </div>
        <div class="schools-list" v-loading="schoolsLoading">
          <el-collapse>
            <el-collapse-item
              v-for="school in filteredSchools"
              :key="school.id"
              :title="school.name"
              :name="school.id"
            >
              <template #title>
                <span class="school-collapse-title">
                  {{ school.name }}
                  <el-tag v-for="tag in school.tags" :key="tag" size="small" type="info" style="margin-left: 6px">
                    {{ tag }}
                  </el-tag>
                  <span class="group-count">（{{ school.groups.length }} 个专业组）</span>
                </span>
              </template>
              <el-table :data="school.groups" size="small" stripe>
                <el-table-column prop="name" label="专业组" min-width="180" />
                <el-table-column prop="entry_rule_text" label="准入规则" min-width="120" />
                <el-table-column prop="preliminary_line" label="实际通过线" width="90" />
                <el-table-column prop="admission_count" label="招生人数" width="90" />
                <el-table-column label="操作" width="80" fixed="right">
                  <template #default="{ row }">
                    <el-button text type="primary" size="small" @click="openEditDialog(school.id, row.id)">
                      编辑
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-collapse-item>
          </el-collapse>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 上传弹窗 -->
    <el-dialog v-model="uploadDialogVisible" title="上传新版本" width="500px" destroy-on-close>
      <el-upload
        drag
        :auto-upload="false"
        :limit="1"
        accept=".json"
        :on-change="handleFileChange"
        :file-list="uploadFileList"
      >
        <el-icon style="font-size: 48px; color: #c0c4cc"><UploadFilled /></el-icon>
        <div style="margin-top: 8px">拖拽文件到此处，或 <em>点击上传</em></div>
        <template #tip>
          <div style="color: #909399; margin-top: 8px">仅支持 .json 格式文件</div>
        </template>
      </el-upload>
      <el-input
        v-model="uploadNote"
        type="textarea"
        placeholder="更新备注（选填）"
        :rows="2"
        style="margin-top: 16px"
      />
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">确认上传</el-button>
      </template>
    </el-dialog>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editDialogVisible" :title="`编辑：${editingSchoolName} - ${editingGroup?.group?.name || ''}`" width="600px" destroy-on-close>
      <el-form :model="editForm" label-width="120px" size="default">
        <el-form-item label="实际通过线">
          <el-input-number v-model="editForm.preliminary_line" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="报考线">
          <el-input-number v-model="editForm.entry_rule_score" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="准入规则原文">
          <el-input v-model="editForm.entry_rule_text" />
        </el-form-item>
        <el-divider content-position="left">等级赋值分</el-divider>
        <el-row :gutter="12">
          <el-col :span="4" v-for="grade in GRADE_OPTIONS" :key="grade">
            <el-form-item :label="grade">
              <el-input-number v-model="editForm.rules[grade]" :min="0" size="small" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="选考科目">
          <el-select v-model="editForm.required_subjects" multiple placeholder="选择科目" style="width: 100%">
            <el-option v-for="s in ['物理','化学','生物','历史','地理','政治','技术']" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="科目模式">
          <el-radio-group v-model="editForm.required_subjects_mode">
            <el-radio value="and">全部满足 (and)</el-radio>
            <el-radio value="or">满足其一 (or)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="去年综合分">
          <el-input-number v-model="editForm.last_year_composite_score" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="招生人数">
          <el-input-number v-model="editForm.admission_count" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="专业描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit">保存（生成新版本）</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.tab-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.school-collapse-title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.group-count {
  color: var(--text-secondary);
  font-size: 13px;
  margin-left: 8px;
}

.schools-list {
  min-height: 200px;
}
</style>

<script setup>
/**
 * SuperView.vue — 高校数据管理页面（仅 super_admin）
 */
import { ref, reactive, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
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
    Message.error(err.message || '获取版本列表失败')
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
    Message.warning('请选择 JSON 文件')
    return
  }
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadFileList.value[0].raw)
    formData.append('note', uploadNote.value)
    const result = await uploadSchools(formData)
    Message.success('上传成功')
    uploadDialogVisible.value = false
    uploadNote.value = ''
    uploadFileList.value = []
    await fetchVersions()
  } catch (err) {
    Message.error(err.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

function handleFileChange(file) {
  // 校验文件类型
  if (!file.name.endsWith('.json')) {
    Message.error('只接受 JSON 文件')
    return false
  }
  uploadFileList.value = [file]
  return false // 阻止自动上传
}

// 回滚
async function handleRollback(version) {
  try {
    Modal.confirm({
      title: '确认回滚',
      content: `确定回滚到 v${version.version_no}（${version.note || '无备注'}）吗？`,
      onOk: async () => {
        await rollbackVersion(version.id)
        Message.success(`已回滚到 v${version.version_no}`)
        await fetchVersions()
      }
    })
  } catch { /* ignored */ }
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
    Message.error(err.message || '获取学校列表失败')
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
    Message.error(err.message || '获取详情失败')
  }
}

async function handleSaveEdit() {
  try {
    const schoolId = editingGroup.value.school_id
    const groupId = editingGroup.value.group.id
    await editGroup(schoolId, groupId, editForm)
    Message.success('编辑保存成功，已生成新版本')
    editDialogVisible.value = false
    await fetchSchools()
    await fetchVersions()
  } catch (err) {
    Message.error(err.message || '保存失败')
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
    <a-tabs v-model:active-key="activeTab">
      <!-- 版本管理 -->
      <a-tab-pane title="📦 版本管理" key="versions">
        <div class="tab-header">
          <a-button type="primary" @click="uploadDialogVisible = true">
            <template #icon><icon-upload /></template>
            上传新版本
          </a-button>
        </div>
        <a-table :data="versions" :loading="versionsLoading" :stripe="true">
          <template #columns>
            <a-table-column title="版本" :width="80">
              <template #cell="{ record }">v{{ record.version_no }}</template>
            </a-table-column>
            <a-table-column title="状态" :width="100" align="center">
              <template #cell="{ record }">
                <a-tag :color="record.is_active ? 'green' : 'gray'" size="small">
                  {{ record.is_active ? '当前使用' : '历史' }}
                </a-tag>
              </template>
            </a-table-column>
            <a-table-column data-index="school_count" title="院校数" :width="80" align="center" />
            <a-table-column data-index="group_count" title="专业组数" :width="90" align="center" />
            <a-table-column data-index="note" title="备注" ellipsis />
            <a-table-column data-index="uploaded_by_name" title="操作人" :width="100" />
            <a-table-column title="上传时间" :width="160">
              <template #cell="{ record }">
                {{ record.uploaded_at ? new Date(record.uploaded_at).toLocaleString('zh-CN') : '-' }}
              </template>
            </a-table-column>
            <a-table-column title="操作" :width="160" fixed="right">
              <template #cell="{ record }">
                <a-button type="text" size="small" @click="handleDownload(record)">下载</a-button>
                <a-button type="text" status="warning" size="small" :disabled="record.is_active" @click="handleRollback(record)">
                  回滚
                </a-button>
              </template>
            </a-table-column>
          </template>
        </a-table>
      </a-tab-pane>

      <!-- 逐条编辑 -->
      <a-tab-pane title="✏️ 逐条编辑" key="edit">
        <div class="tab-header">
          <a-input
            v-model="searchKey"
            placeholder="搜索院校名称或标签..."
            allow-clear
            style="max-width: 320px"
            @input="filterSchools"
          >
            <template #prefix><icon-search /></template>
          </a-input>
        </div>
        <div class="schools-list">
          <a-spin :loading="schoolsLoading" style="width: 100%; min-height: 200px;">
            <a-collapse>
              <a-collapse-item
                v-for="school in filteredSchools"
                :key="school.id"
                :header="school.name"
              >
                <template #header>
                  <span class="school-collapse-title">
                    {{ school.name }}
                    <a-tag v-for="tag in school.tags" :key="tag" size="small" color="arcoblue" style="margin-left: 6px">
                      {{ tag }}
                    </a-tag>
                    <span class="group-count">（{{ school.groups.length }} 个专业组）</span>
                  </span>
                </template>
                <a-table :data="school.groups" size="small" :stripe="true">
                  <template #columns>
                    <a-table-column data-index="name" title="专业组" :width="180" />
                    <a-table-column data-index="entry_rule_text" title="准入规则" :width="120" />
                    <a-table-column data-index="preliminary_line" title="实际通过线" :width="90" />
                    <a-table-column data-index="admission_count" title="招生人数" :width="90" />
                    <a-table-column title="操作" :width="80" fixed="right">
                      <template #cell="{ record }">
                        <a-button type="text" size="small" @click="openEditDialog(school.id, record.id)">
                          编辑
                        </a-button>
                      </template>
                    </a-table-column>
                  </template>
                </a-table>
              </a-collapse-item>
            </a-collapse>
          </a-spin>
        </div>
      </a-tab-pane>
    </a-tabs>

    <!-- 上传弹窗 -->
    <a-modal v-model:visible="uploadDialogVisible" title="上传新版本" :width="500" unmount-on-close @cancel="uploadDialogVisible = false" @ok="handleUpload" :ok-loading="uploading" ok-text="确认上传">
      <a-upload
        draggable
        :auto-upload="false"
        :limit="1"
        accept=".json"
        @change="(_, currentFile) => handleFileChange(currentFile.file)"
        :file-list="uploadFileList"
      />
      <a-textarea
        v-model="uploadNote"
        placeholder="更新备注（选填）"
        :auto-size="{ minRows: 2, maxRows: 4 }"
        style="margin-top: 16px"
      />
    </a-modal>

    <!-- 编辑弹窗 -->
    <a-modal v-model:visible="editDialogVisible" :title="`编辑：${editingSchoolName} - ${editingGroup?.group?.name || ''}`" :width="600" unmount-on-close @cancel="editDialogVisible = false" @ok="handleSaveEdit" ok-text="保存（生成新版本）">
      <a-form :model="editForm" auto-label-width size="medium">
        <a-form-item label="实际通过线">
          <a-input-number v-model="editForm.preliminary_line" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item label="报考线">
          <a-input-number v-model="editForm.entry_rule_score" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item label="准入规则原文">
          <a-input v-model="editForm.entry_rule_text" />
        </a-form-item>
        <a-divider orientation="left">等级赋值分</a-divider>
        <a-row :gutter="12">
          <a-col :span="4" v-for="grade in GRADE_OPTIONS" :key="grade">
            <a-form-item :label="grade">
              <a-input-number v-model="editForm.rules[grade]" :min="0" size="small" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="选考科目">
          <a-select v-model="editForm.required_subjects" multiple placeholder="选择科目" style="width: 100%">
            <a-option v-for="s in ['物理','化学','生物','历史','地理','政治','技术']" :key="s" :label="s" :value="s" />
          </a-select>
        </a-form-item>
        <a-form-item label="科目模式">
          <a-radio-group v-model="editForm.required_subjects_mode">
            <a-radio value="and">全部满足 (and)</a-radio>
            <a-radio value="or">满足其一 (or)</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="去年综合分">
          <a-input-number v-model="editForm.last_year_composite_score" :min="0" :precision="2" style="width: 100%" />
        </a-form-item>
        <a-form-item label="招生人数">
          <a-input-number v-model="editForm.admission_count" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item label="专业描述">
          <a-textarea v-model="editForm.description" :auto-size="{ minRows: 3, maxRows: 6 }" />
        </a-form-item>
      </a-form>
    </a-modal>
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

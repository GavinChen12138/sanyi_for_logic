<script setup>
/**
 * MatchView.vue — 成绩录入 + 匹配结果展示
 */
import { ref, reactive, computed, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import { matchSchools } from '@/api/match'
import ResultCard from '@/components/ResultCard.vue'
import { GRADE_OPTIONS, SUBJECT_OPTIONS, ALL_XUEKAO_SUBJECTS, STATUS_COLOR_MAP, FILTER_TAGS } from '@/constants'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'

const formRef = ref(null)
const loading = ref(false)
const results = ref(null)

const form = reactive({
  selectedSubjects: [],
  xuekaoGrades: {}
})

const selectedTags = ref([]) // 选中的标签

// 所有需要填写的学考科目（10门必填）
const allXuekaoSubjects = computed(() => {
  return ALL_XUEKAO_SUBJECTS
})

const rules = {
  selectedSubjects: [
    { type: 'array', len: 3, required: true, message: '请选择3门选考科目', trigger: 'change' }
  ]
}

// 统计信息
const summary = computed(() => {
  if (!results.value) return null
  return {
    可报考: results.value['可报考']?.length || 0,
    待确认: results.value['待确认']?.length || 0,
    不可报考: results.value['不可报考']?.length || 0,
  }
})

// 当前筛选显示的状态
const activeTab = ref('可报考')

// 切换筛选标签
function toggleTag(tag) {
  const index = selectedTags.value.indexOf(tag)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tag)
  }
}

// 当前展示的结果
const displayResults = computed(() => {
  if (!results.value) return []
  let list = results.value[activeTab.value] || []
  if (selectedTags.value.length > 0) {
    list = list.filter(item => {
      if (!item.tags) return false
      return selectedTags.value.some(t => item.tags.includes(t))
    })
  }
  return list
})

// 按学校分组的展示结果
const groupedResults = computed(() => {
  if (displayResults.value.length === 0) return []
  
  const groupsRecord = {}
  displayResults.value.forEach(item => {
    if (!groupsRecord[item.school_name]) {
      groupsRecord[item.school_name] = {
        school_name: item.school_name,
        tags: item.tags || [],
        items: []
      }
    }
    groupsRecord[item.school_name].items.push(item)
  })
  return Object.values(groupsRecord)
})

async function handleSubmit() {
  await formRef.value.validate()

  // 检查学考等级是否全部填写
  for (const subject of allXuekaoSubjects.value) {
    if (!form.xuekaoGrades[subject]) {
      Message.warning(`请选择 ${subject} 的学考等级`)
      return
    }
  }

  loading.value = true
  try {
    const data = await matchSchools({
      selected_subjects: form.selectedSubjects,
      xuekao_grades: form.xuekaoGrades
    })
    results.value = data
    activeTab.value = '可报考'
    Message.success(`匹配完成：可报考 ${data['可报考'].length}，待确认 ${data['待确认'].length}，不可报考 ${data['不可报考'].length}`)
  } catch (err) {
    Message.error(err.message || '匹配失败')
  } finally {
    loading.value = false
  }
}

function handleReset() {
  formRef.value.resetFields()
  form.xuekaoGrades = {}
  results.value = null
}

// 快速全选等级
function fillAllGrades(grade) {
  allXuekaoSubjects.value.forEach(subject => {
    form.xuekaoGrades[subject] = grade
  })
}

// 下载 Excel
function handleDownloadExcel() {
  if (!results.value) return

  const rows = []
  for (const status of ['可报考', '待确认', '不可报考']) {
    for (const r of results.value[status] || []) {
      rows.push({
        '状态': status,
        '院校': r.school_name,
        '专业组': r.group_name,
        '标签': (r.tags || []).join('、'),
        '实际通过线': r.passing_line.preliminary_line || '待定',
        '通过线差值': r.passing_line.gap,
        '报考线': r.xuekao.score_line ?? r.xuekao.entry_rule_text,
        '报考线差值': r.xuekao.gap ?? '需人工核查',
        '学考赋值分': r.xuekao.student_score,
        '规则类型': r.xuekao.rule_type === 'score' ? '数值' : '文字',
        '去年综合分': r.meta.last_year_composite_score || '暂无',
        '满分基准': r.meta.total_score,
        '招生人数': r.meta.admission_count,
        '选考要求': (r.meta.required_subjects || []).join('+'),
        '科目模式': r.meta.required_subjects_mode === 'and' ? '全部满足' : '满足其一',
        '备注': r.status_reason,
        '描述': r.meta.description
      })
    }
  }

  const ws = XLSX.utils.json_to_sheet(rows)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '匹配结果')
  const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  saveAs(new Blob([wbout], { type: 'application/octet-stream' }), '三位一体匹配结果.xlsx')
  Message.success('Excel 下载成功')
}
</script>

<template>
  <div class="page-container">
    <!-- 录入表单 -->
    <a-card class="form-card card-accent-top" hoverable>
      <template #title>
        <div class="card-header">
          <div class="card-title-group">
            <icon-edit class="card-title-icon" />
            <span>成绩录入</span>
          </div>
          <a-button type="text" size="small" @click="handleReset">
            <template #icon><icon-refresh /></template>
            重置
          </a-button>
        </div>
      </template>

      <a-form
        ref="formRef"
        :model="form"
        :rules="rules"
        auto-label-width
        layout="vertical"
      >
        <!-- 选考科目 -->
        <div class="section-header">
          <icon-bookmark class="section-icon" />
          <span class="section-title">选考科目</span>
          <span class="section-hint">请选择 3 门</span>
        </div>
        <a-form-item label="" field="selectedSubjects" hide-label>
          <div class="subject-pills">
            <a-checkbox-group v-model="form.selectedSubjects" :max="3">
              <a-checkbox
                v-for="subject in SUBJECT_OPTIONS"
                :key="subject"
                :value="subject"
                class="subject-pill"
              >
                {{ subject }}
              </a-checkbox>
            </a-checkbox-group>
          </div>
        </a-form-item>

        <!-- 学考等级 -->
        <div class="section-header">
          <icon-star class="section-icon" />
          <span class="section-title">学考等级</span>
          <div class="quick-fill">
            <a-button
              v-for="g in ['A', 'B', 'C', 'D']"
              :key="g"
              size="mini"
              type="outline"
              class="quick-fill-btn"
              @click="fillAllGrades(g)"
            >
              全{{ g }}
            </a-button>
          </div>
        </div>
        <a-row :gutter="[12, 4]">
          <a-col
            v-for="subject in allXuekaoSubjects"
            :key="subject"
            :span="8"
            :xs="12"
          >
            <a-form-item :label="subject" class="grade-item">
              <a-radio-group v-model="form.xuekaoGrades[subject]" type="button" size="small">
                <a-radio
                  v-for="grade in GRADE_OPTIONS"
                  :key="grade"
                  :value="grade"
                >{{ grade }}</a-radio>
              </a-radio-group>
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 提交 -->
        <a-form-item class="submit-row">
          <a-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleSubmit"
            long
            class="submit-btn"
          >
            <template #icon><icon-search /></template>
            开始匹配
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 匹配结果 -->
    <template v-if="results">
      <!-- 统计概览 -->
      <a-row :gutter="16" class="summary-row">
        <a-col :span="8">
          <div
            class="stat-card stat-card--success hover-card"
            :class="{ 'stat-card--active': activeTab === '可报考' }"
            @click="activeTab = '可报考'"
          >
            <div class="stat-count">{{ summary.可报考 }}</div>
            <div class="stat-label">可报考</div>
          </div>
        </a-col>
        <a-col :span="8">
          <div
            class="stat-card stat-card--warning hover-card"
            :class="{ 'stat-card--active': activeTab === '待确认' }"
            @click="activeTab = '待确认'"
          >
            <div class="stat-count">{{ summary.待确认 }}</div>
            <div class="stat-label">待确认</div>
          </div>
        </a-col>
        <a-col :span="8">
          <div
            class="stat-card stat-card--danger hover-card"
            :class="{ 'stat-card--active': activeTab === '不可报考' }"
            @click="activeTab = '不可报考'"
          >
            <div class="stat-count">{{ summary.不可报考 }}</div>
            <div class="stat-label">不可报考</div>
          </div>
        </a-col>
      </a-row>

      <!-- 操作栏 -->
      <div class="action-bar">
        <div class="action-left">
          <a-radio-group v-model="activeTab" type="button" size="large">
            <a-radio v-for="status in ['可报考', '待确认', '不可报考']" :key="status" :value="status">
              {{ status }}（{{ summary[status] }}）
            </a-radio>
          </a-radio-group>
        </div>
        <a-button type="primary" status="success" @click="handleDownloadExcel" class="download-btn">
          <template #icon><icon-download /></template>
          下载 Excel
        </a-button>
      </div>

      <!-- 标签筛选 -->
      <div class="filter-section">
        <span class="filter-label">
          <icon-filter class="filter-icon" />
          标签筛选
        </span>
        <div class="filter-tags">
          <a-tag 
            v-for="tag in FILTER_TAGS" 
            :key="tag" 
            size="medium" 
            :color="selectedTags.includes(tag) ? 'arcoblue' : ''" 
            :bordered="true" 
            class="filter-tag-pill"
            @click="toggleTag(tag)"
          >
            {{ tag }}
          </a-tag>
        </div>
      </div>

      <!-- 结果列表 (按学校合并展示) -->
      <transition-group name="list" tag="div" class="results-list" v-if="groupedResults.length > 0">
        <a-card
          v-for="school in groupedResults"
          :key="school.school_name"
          class="school-group-card"
          :bordered="true"
        >
          <template #title>
            <div class="school-header">
              <span class="school-name">{{ school.school_name }}</span>
              <div class="school-tags" v-if="school.tags.length">
                <a-tag v-for="tag in school.tags" :key="tag" size="small" color="arcoblue" bordered>
                  {{ tag }}
                </a-tag>
              </div>
            </div>
          </template>
          <div class="group-items">
            <ResultCard
              v-for="item in school.items"
              :key="item.group_id"
              :result="item"
            />
          </div>
        </a-card>
      </transition-group>

      <a-empty v-if="groupedResults.length === 0" description="暂无匹配结果" />
    </template>
  </div>
</template>

<style scoped>
/* ── 表单卡片 ── */
.form-card {
  margin-bottom: 24px;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.card-title-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title-icon {
  color: var(--primary-color);
  font-size: 18px;
}

/* ── 段落标题 ── */
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  margin-top: 8px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-light);
}

.section-icon {
  color: var(--primary-color);
  font-size: 16px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-left: auto;
}

/* ── 科目 Pill 选择 ── */
.subject-pills {
  margin-bottom: 8px;
}

.subject-pills :deep(.arco-checkbox) {
  padding: 6px 16px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border-color);
  margin-right: 8px;
  margin-bottom: 8px;
  transition: all var(--transition-normal);
  cursor: pointer;
}

.subject-pills :deep(.arco-checkbox:hover) {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.subject-pills :deep(.arco-checkbox.arco-checkbox-checked) {
  background: var(--primary-light);
  border-color: var(--primary-color);
  color: var(--primary-color);
  font-weight: 600;
}

/* ── 快速填入 ── */
.quick-fill {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
}

.quick-fill-btn {
  border-radius: var(--radius-pill) !important;
  font-size: 12px;
  padding: 0 10px !important;
}

/* ── 学考等级 ── */
.grade-item {
  margin-bottom: 8px;
}

.grade-item :deep(.arco-radio-group-button .arco-radio-button) {
  border-radius: var(--radius-sm) !important;
}

/* ── 提交按钮 ── */
.submit-row {
  margin-top: 12px;
}

.submit-btn {
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: var(--radius-md);
  transition: box-shadow var(--transition-normal);
}

.submit-btn:hover {
  box-shadow: 0 4px 16px rgba(22, 93, 255, 0.35);
}

/* ── 统计概览 ── */
.summary-row {
  margin-bottom: 20px;
}

.stat-card--active {
  box-shadow: var(--shadow-md) !important;
  transform: scale(1.02);
}

/* ── 操作栏 ── */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  flex-wrap: wrap;
  gap: 12px;
}

.action-left {
  flex: 1;
  min-width: 0;
}

.download-btn {
  border-radius: var(--radius-md);
  font-weight: 500;
}

/* ── 标签筛选 ── */
.filter-section {
  margin-bottom: 20px;
  background: white;
  padding: 14px 16px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

.filter-icon {
  font-size: 14px;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-tag-pill {
  cursor: pointer;
  border-radius: var(--radius-pill) !important;
  transition: all var(--transition-normal);
}

/* ── 结果列表 ── */
.results-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.school-group-card {
  border-radius: var(--radius-lg);
  overflow: hidden;
}

/* 覆盖 a-card 的 header padding 以紧凑显示 */
:deep(.school-group-card > .arco-card-header) {
  padding: 10px 16px;
  background: linear-gradient(135deg, #FAFBFC 0%, #F7F8FA 100%);
  border-bottom: 1px solid var(--border-color);
  height: auto;
}

:deep(.school-group-card > .arco-card-body) {
  padding: 10px 12px;
  background: #F7F8FA;
}

.school-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.school-header .school-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.school-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.group-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
</style>

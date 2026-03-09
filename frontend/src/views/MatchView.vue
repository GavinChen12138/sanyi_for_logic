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
    <a-card class="form-card" hoverable>
      <template #title>
        <div class="card-header">
          <span>成绩录入</span>
          <div>
            <a-button type="text" @click="handleReset">重置</a-button>
          </div>
        </div>
      </template>

      <a-form
        ref="formRef"
        :model="form"
        :rules="rules"
        auto-label-width
        layout="vertical"
      >
        <!-- 高考成绩（已移除） -->

        <!-- 选考科目 -->
        <a-divider orientation="left">选考科目</a-divider>
        <a-form-item label="7选3" field="selectedSubjects">
          <a-checkbox-group v-model="form.selectedSubjects" :max="3">
            <a-checkbox
              v-for="subject in SUBJECT_OPTIONS"
              :key="subject"
              :value="subject"
            >
              {{ subject }}
            </a-checkbox>
          </a-checkbox-group>
        </a-form-item>

        <!-- 学考等级 -->
        <a-divider orientation="left">学考等级</a-divider>
        <div class="quick-fill">
          <span class="quick-fill-label">快速填入：</span>
          <a-button v-for="g in ['A', 'B', 'C', 'D']" :key="g" size="small" @click="fillAllGrades(g)">全选{{ g }}</a-button>
        </div>
        <a-row :gutter="16">
          <a-col
            v-for="subject in allXuekaoSubjects"
            :key="subject"
            :span="8"
            :xs="12"
          >
            <a-form-item :label="subject">
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
        <a-form-item>
          <a-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleSubmit"
            long
          >
            开始匹配
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 匹配结果 -->
    <template v-if="results">
      <!-- 标签筛选 -->
      <div class="filter-section">
        <a-checkbox-group v-model="selectedTags">
          <a-checkbox v-for="tag in FILTER_TAGS" :key="tag" :value="tag">
            {{ tag }}
          </a-checkbox>
        </a-checkbox-group>
      </div>

      <!-- 统计概览 -->
      <a-row :gutter="16" class="summary-row">
        <a-col :span="8" v-for="(count, status) in summary" :key="status">
          <a-card
            hoverable
            class="summary-card hover-card"
            :class="'summary-card--' + status"
            @click="activeTab = status"
          >
            <div class="summary-count">{{ count }}</div>
            <div class="summary-label">{{ status }}</div>
          </a-card>
        </a-col>
      </a-row>

      <!-- 操作栏 -->
      <div class="action-bar">
        <a-radio-group v-model="activeTab" type="button" size="large">
          <a-radio v-for="status in ['可报考', '待确认', '不可报考']" :key="status" :value="status">
            {{ status }}（{{ summary[status] }}）
          </a-radio>
        </a-radio-group>
        <a-button type="primary" status="success" @click="handleDownloadExcel">
          <template #icon><icon-download /></template>
          下载 Excel
        </a-button>
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
.form-card {
  margin-bottom: 24px;
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.filter-section {
  margin-bottom: 20px;
  background: white;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.summary-row {
  margin-bottom: 20px;
}

.summary-card {
  text-align: center;
  padding: 16px 0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.summary-card--可报考 { border-left: 4px solid var(--success-color); }
.summary-card--待确认 { border-left: 4px solid var(--warning-color); }
.summary-card--不可报考 { border-left: 4px solid var(--danger-color); }

.summary-count {
  font-size: 32px;
  font-weight: 700;
}

.summary-card--可报考 .summary-count { color: var(--success-color); }
.summary-card--待确认 .summary-count { color: var(--warning-color); }
.summary-card--不可报考 .summary-count { color: var(--danger-color); }

.summary-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.school-group-card {
  border-radius: 12px;
  background: var(--bg-color);
}

/* 覆盖 a-card 的 header padding 以紧凑显示 */
:deep(.school-group-card > .arco-card-header) {
  padding: 8px 16px;
  background-color: #fcfcfc;
  border-bottom: 1px solid var(--color-border);
  height: auto;
}

:deep(.school-group-card > .arco-card-body) {
  padding: 10px 12px;
  background-color: #f5f7fa;
}

.school-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.school-header .school-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
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

.quick-fill {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.quick-fill-label {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
}
</style>

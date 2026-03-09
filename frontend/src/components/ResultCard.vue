<script setup>
/**
 * ResultCard.vue — 单条匹配结果展示（紧凑行样式）
 */
import { computed } from 'vue'
import { STATUS_COLOR_MAP } from '@/constants'

const props = defineProps({
  result: {
    type: Object,
    required: true
  }
})

// 颜色映射 (Element Plus 类型转为 Arco Design 颜色)
const arcoColorMap = {
  success: 'green',
  warning: 'orange',
  danger: 'red',
  info: 'gray'
}

const statusColor = computed(() => arcoColorMap[STATUS_COLOR_MAP[props.result.status] || 'info'])

// 实际通过线展示
const passingDisplay = computed(() => {
  const g = props.result.passing_line
  if (!g.preliminary_line || g.preliminary_line === 0) {
    return { line: '待定', gap: null, color: arcoColorMap['info'] }
  }
  return {
    line: g.preliminary_line,
    gap: g.gap,
    color: g.gap >= 0 ? arcoColorMap['success'] : arcoColorMap['warning']
  }
})

// 学考展示
const xuekaoDisplay = computed(() => {
  const x = props.result.xuekao
  if (x.rule_type === 'text') {
    return { text: x.entry_rule_text, isText: true, studentScore: x.student_score }
  }
  return {
    studentScore: x.student_score,
    scoreLine: x.score_line,
    gap: x.gap,
    isText: false,
    color: x.gap >= 0 ? arcoColorMap['success'] : (x.gap >= -5 ? arcoColorMap['warning'] : arcoColorMap['danger'])
  }
})

// 去年综合分
const lastYearDisplay = computed(() => {
  const score = props.result.meta.last_year_composite_score
  if (!score || score === 0) return '—'
  return `${score}（满分${props.result.meta.total_score}）`
})
</script>

<template>
  <div class="result-row">
    <!-- 专业组名 + 状态标签 -->
    <div class="row-main">
      <div class="row-title">
        <span class="group-name">{{ result.group_name }}</span>
        <a-tag :color="statusColor" size="small" class="status-tag" style="border-radius: 12px;">
          {{ result.status }}
        </a-tag>
      </div>

      <!-- 核心数据：用 inline 字段并排 -->
      <div class="row-fields">
        <!-- 报考线 -->
        <div class="field">
          <span class="field-label">报考线</span>
          <template v-if="xuekaoDisplay.isText">
            <span class="field-value">{{ xuekaoDisplay.studentScore }}</span>
            <a-tag color="orange" size="small" class="field-tag">人工核查</a-tag>
            <span class="field-note">{{ xuekaoDisplay.text }}</span>
          </template>
          <template v-else>
            <span class="field-value">{{ xuekaoDisplay.studentScore }}</span>
            <span class="field-slash">/ {{ xuekaoDisplay.scoreLine }}</span>
            <a-tag :color="xuekaoDisplay.color" size="small" class="field-tag">
              {{ xuekaoDisplay.gap >= 0 ? '+' : '' }}{{ xuekaoDisplay.gap }}
            </a-tag>
          </template>
        </div>

        <!-- 实际通过线 -->
        <div class="field">
          <span class="field-label">通过线</span>
          <span class="field-value">{{ result.xuekao.student_score }}</span>
          <template v-if="passingDisplay.line !== '待定'">
            <span class="field-slash">/ {{ passingDisplay.line }}</span>
            <a-tag :color="passingDisplay.color" size="small" class="field-tag">
              {{ passingDisplay.gap >= 0 ? '+' : '' }}{{ passingDisplay.gap }}
            </a-tag>
          </template>
          <template v-else>
            <span class="field-slash field-pending">/ 待定</span>
          </template>
        </div>

        <!-- 选考要求 -->
        <div class="field" v-if="result.meta.required_subjects?.length">
          <span class="field-label">选考</span>
          <span class="field-text">
            {{ result.meta.required_subjects.join(result.meta.required_subjects_mode === 'and' ? '+' : '/') }}
          </span>
          <a-tag size="small" color="gray" class="field-tag">
            {{ result.meta.required_subjects_mode === 'and' ? '全部' : '其一' }}
          </a-tag>
        </div>

        <!-- 去年综合分 -->
        <div class="field">
          <span class="field-label">去年</span>
          <span class="field-text">{{ lastYearDisplay }}</span>
        </div>

        <!-- 招生人数 -->
        <div class="field" v-if="result.meta.admission_count">
          <span class="field-label">招生</span>
          <span class="field-text">{{ result.meta.admission_count }} 人</span>
        </div>
      </div>

      <!-- 说明（单独一行，仅在有内容时显示） -->
      <div class="row-reason" v-if="result.status_reason">
        <span class="field-label">说明：</span>
        <span class="reason-text">{{ result.status_reason }}</span>
      </div>

      <!-- 专业描述（折叠） -->
      <a-collapse v-if="result.meta.description" class="desc-collapse" :bordered="false">
        <a-collapse-item header="专业描述" key="1">
          <p class="description-text">{{ result.meta.description }}</p>
        </a-collapse-item>
      </a-collapse>
    </div>
  </div>
</template>

<style scoped>
.result-row {
  padding: 10px 14px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  transition: box-shadow 0.2s;
}

.result-row:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.row-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.row-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.status-tag {
  flex-shrink: 0;
}

/* 核心数据字段横向排列 */
.row-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 20px;
}

.field {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.field-label {
  color: var(--text-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.field-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.field-slash {
  font-size: 13px;
  color: var(--text-secondary);
}

.field-pending {
  color: var(--el-text-color-placeholder);
}

.field-text {
  font-size: 13px;
  color: var(--text-primary);
}

.field-tag {
  flex-shrink: 0;
}

.field-note {
  font-size: 12px;
  color: var(--warning-color);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-reason {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  font-size: 12px;
  color: var(--warning-color);
}

.reason-text {
  color: var(--warning-color);
  font-size: 12px;
}

.desc-collapse {
  margin-top: 2px;
  border: none;
}

.description-text {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}
</style>

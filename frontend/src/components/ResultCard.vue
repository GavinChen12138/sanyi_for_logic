<script setup>
/**
 * ResultCard.vue — 单条匹配结果展示卡片
 */
import { computed } from 'vue'
import { STATUS_COLOR_MAP } from '@/constants'

const props = defineProps({
  result: {
    type: Object,
    required: true
  }
})

const statusType = computed(() => STATUS_COLOR_MAP[props.result.status] || 'info')

// 实际通过线展示 (原 gaokaoDisplay)
const passingDisplay = computed(() => {
  const g = props.result.passing_line
  if (!g.preliminary_line || g.preliminary_line === 0) {
    return { line: '待定', gap: null, color: 'info' }
  }
  return {
    line: g.preliminary_line,
    gap: g.gap,
    color: g.gap >= 0 ? 'success' : 'warning'
  }
})

// 学考展示
const xuekaoDisplay = computed(() => {
  const x = props.result.xuekao
  if (x.rule_type === 'text') {
    return { text: x.entry_rule_text, isText: true }
  }
  return {
    studentScore: x.student_score,
    scoreLine: x.score_line,
    gap: x.gap,
    isText: false,
    color: x.gap >= 0 ? 'success' : (x.gap >= -5 ? 'warning' : 'danger')
  }
})

// 去年综合分
const lastYearDisplay = computed(() => {
  const score = props.result.meta.last_year_composite_score
  if (!score || score === 0) return '暂无历史数据'
  return `${score}（满分${props.result.meta.total_score}）`
})
</script>

<template>
  <el-card class="result-card hover-card" shadow="hover">
    <div class="card-top">
      <div class="card-title-row">
        <div class="card-title">
          <span class="group-name">{{ result.group_name }}</span>
        </div>
        <el-tag :type="statusType" size="default" effect="dark" round>
          {{ result.status }}
        </el-tag>
      </div>
    </div>

    <el-divider style="margin: 12px 0" />

    <div class="card-body">
      <el-row :gutter="20">
        <!-- 报考线 -->
        <el-col :span="12" :xs="24">
          <div class="dimension">
            <div class="dim-label">📊 报考线</div>
            <template v-if="xuekaoDisplay.isText">
              <div class="dim-value">
                <span class="score">{{ result.xuekao.student_score }}</span>
                <span class="dim-note">分</span>
              </div>
              <div class="dim-rule">
                <el-tag type="warning" size="small">需人工核查</el-tag>
                <span class="rule-text">{{ xuekaoDisplay.text }}</span>
              </div>
            </template>
            <template v-else>
              <div class="dim-value">
                <span class="score">{{ xuekaoDisplay.studentScore }}</span>
                <span class="dim-note"> / {{ xuekaoDisplay.scoreLine }}</span>
                <el-tag :type="xuekaoDisplay.color" size="small" style="margin-left: 8px">
                  {{ xuekaoDisplay.gap >= 0 ? '+' : '' }}{{ xuekaoDisplay.gap }}
                </el-tag>
              </div>
            </template>
          </div>
        </el-col>

        <!-- 实际通过线 -->
        <el-col :span="12" :xs="24">
          <div class="dimension">
            <div class="dim-label">🎓 实际通过线</div>
            <div class="dim-value">
              <span class="score">{{ result.xuekao.student_score }}</span>
              <template v-if="passingDisplay.line !== '待定'">
                <span class="dim-note"> / {{ passingDisplay.line }}</span>
                <el-tag :type="passingDisplay.color" size="small" style="margin-left: 8px">
                  {{ passingDisplay.gap >= 0 ? '+' : '' }}{{ passingDisplay.gap }}
                </el-tag>
              </template>
              <template v-else>
                <span class="dim-note"> / 待定</span>
              </template>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 详细信息 -->
      <div class="detail-row">
        <div class="detail-item" v-if="result.meta.required_subjects?.length">
          <span class="detail-label">选考要求：</span>
          <span>{{ result.meta.required_subjects.join(result.meta.required_subjects_mode === 'and' ? ' + ' : ' / ') }}</span>
          <el-tag size="small" type="info" style="margin-left: 4px">
            {{ result.meta.required_subjects_mode === 'and' ? '全部满足' : '满足其一' }}
          </el-tag>
        </div>
        <div class="detail-item">
          <span class="detail-label">去年综合分：</span>
          <span>{{ lastYearDisplay }}</span>
        </div>
        <div class="detail-item" v-if="result.meta.admission_count">
          <span class="detail-label">招生人数：</span>
          <span>{{ result.meta.admission_count }} 人</span>
        </div>
        <div class="detail-item" v-if="result.status_reason">
          <span class="detail-label">说明：</span>
          <span class="status-reason">{{ result.status_reason }}</span>
        </div>
      </div>

      <!-- 专业描述（可折叠） -->
      <el-collapse v-if="result.meta.description">
        <el-collapse-item title="专业描述">
          <p class="description-text">{{ result.meta.description }}</p>
        </el-collapse-item>
      </el-collapse>
    </div>
  </el-card>
</template>

<style scoped>
.result-card {
  border-radius: 12px;
  overflow: hidden;
}

.card-top {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.group-name {
  color: var(--text-primary);
  font-size: 15px;
}

.dimension {
  margin-bottom: 12px;
}

.dim-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.dim-value {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 4px;
}

.score {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.dim-note {
  font-size: 14px;
  color: var(--text-secondary);
}

.dim-rule {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.rule-text {
  font-size: 13px;
  color: var(--warning-color);
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}

.detail-item {
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.detail-label {
  color: var(--text-secondary);
  font-weight: 500;
}

.status-reason {
  color: var(--warning-color);
}

.description-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}
</style>

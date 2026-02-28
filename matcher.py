"""
浙江三位一体 核心匹配逻辑
matcher.py

数据说明（来自 schools.json 实际结构）：
- preliminary_line  : 高考预审分数线
- score_line        : 学考赋值分门槛（entry_rule.score，数值型）
- rules             : 该校各等级赋值分 {"A": 10, "B": 8, "C": 6, "D": 4, "E": 0}
- entry_rule_text   : 部分院校用描述性文字表达准入规则（如"A+B大于等于5"），
                      这类无法自动计算，标记为 rule_type="text"，展示原文供规划师人工判断
- total_score       : 满分基准（100 或 750），用于归一化展示
- required_subjects + required_subjects_mode: 选考科目限制
"""

import json
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

# ── 等级顺序 ──────────────────────────────────────────────
GRADE_ORDER = ["A", "B", "C", "D", "E"]

# ── 配置项（可由后端 config 文件覆盖） ────────────────────
GAOKAO_NEAR_GAP = 10    # 高考接近线：差距 ≤ 10 分视为接近
XUEKAO_NEAR_GAP = 5     # 学考接近线：赋值分差距 ≤ 5 分视为接近


# ── 数据模型 ─────────────────────────────────────────────
@dataclass
class StudentInput:
    selected_subjects: list[str]             # 选考科目，如 ["物理", "化学", "生物"]
    xuekao_grades: dict[str, str]            # 学考等级，如 {"语文": "A", "数学": "B", ...}


@dataclass
class MatchResult:
    school_id: str
    school_name: str
    group_id: str
    group_name: str
    tags: list[str]

    # 实际通过线维度
    preliminary_line: float     # 该组实际通过线
    preliminary_gap: float      # 正数=超出，负数=不足

    # 学考维度
    student_xuekao_score: float     # 学生在该校规则下的赋值分
    score_line: Optional[float]     # 该组学考赋值分门槛（None 表示无固定数值）
    xuekao_gap: Optional[float]     # 正数=超出，负数=不足（None 表示文字规则）
    rule_type: str                  # "score" | "text"
    entry_rule_text: str            # 原始规则文字，供展示

    # 综合判断
    status: str                     # "可报考" | "待确认" | "不可报考"
    status_reason: str              # 待确认/不可报考时的简短说明

    # 其他展示信息
    total_score: int                # 满分基准（100 或 750）
    last_year_composite_score: float
    admission_count: int
    description: str
    required_subjects: list[str]
    required_subjects_mode: str
    weights: dict                   # calcConfig.weights


# ── 核心匹配器 ────────────────────────────────────────────
class Matcher:
    def __init__(self, schools_data: list[dict]):
        self.schools = schools_data

    def match(self, student: StudentInput) -> dict:
        """
        返回:
        {
            "可报考": [MatchResult, ...],
            "待确认": [MatchResult, ...],
            "不可报考": [MatchResult, ...],
        }
        """
        results = {"可报考": [], "待确认": [], "不可报考": []}

        for school in self.schools:
            for group in school.get("groups", []):
                result = self._evaluate_group(school, group, student)
                results[result.status].append(result)

        # 每个分组内部按 preliminary_line 降序（越难越前）
        for status in results:
            results[status].sort(key=lambda r: r.preliminary_line, reverse=True)

        return results

    def _evaluate_group(
        self, school: dict, group: dict, student: StudentInput
    ) -> MatchResult:
        school_id = school["id"]
        school_name = school["name"]
        tags = school.get("tags", [])
        calc = school.get("calcConfig", {})
        weights = calc.get("weights", {})
        total_score = calc.get("total_score", 100)

        group_id = group["id"]
        group_name = group["name"]
        rules = group.get("rules", {})
        required_subjects = group.get("required_subjects", [])
        required_subjects_mode = group.get("required_subjects_mode", "or")
        preliminary_line = group.get("preliminary_line") or 0
        entry_rule = group.get("entry_rule", {})
        entry_rule_text = group.get("entry_rule_text", "")
        last_year_score = group.get("last_year_composite_score", 0)
        admission_count = group.get("admission_count", 0)
        description = group.get("description", "")

        # ── Step 1: 选考科目检查 ──────────────────────────
        subject_ok = self._check_subjects(
            student.selected_subjects, required_subjects, required_subjects_mode
        )

        # ── Step 2: 计算学考赋值分 ───────────────────────
        student_xuekao_score = self._calc_xuekao_score(
            student.xuekao_grades, rules
        )

        # ── Step 3: 判断学考门槛类型 ─────────────────────
        rule_type = entry_rule.get("kind", "score")
        score_line_val = entry_rule.get("score")  # 可能为 null/None

        # 判断是否为纯数值门槛还是文字描述
        is_text_rule = (
            rule_type != "score"
            or score_line_val is None
            or not self._is_numeric_rule(entry_rule_text)
        )

        if is_text_rule:
            rule_type = "text"
            score_line = None
            xuekao_gap = None
        else:
            rule_type = "score"
            score_line = float(score_line_val)
            xuekao_gap = student_xuekao_score - score_line

        # ── Step 4: 实际通过线维度 ─────────────────────────────
        preliminary_gap = student_xuekao_score - preliminary_line

        status, reason = self._determine_status(
            subject_ok=subject_ok,
            preliminary_gap=preliminary_gap,
            xuekao_gap=xuekao_gap,
            is_text_rule=is_text_rule,
        )

        return MatchResult(
            school_id=school_id,
            school_name=school_name,
            group_id=group_id,
            group_name=group_name,
            tags=tags,
            preliminary_line=preliminary_line,
            preliminary_gap=round(preliminary_gap, 2),
            student_xuekao_score=round(student_xuekao_score, 2),
            score_line=score_line,
            xuekao_gap=round(xuekao_gap, 2) if xuekao_gap is not None else None,
            rule_type=rule_type,
            entry_rule_text=entry_rule_text,
            status=status,
            status_reason=reason,
            total_score=total_score,
            last_year_composite_score=last_year_score,
            admission_count=admission_count,
            description=description,
            required_subjects=required_subjects,
            required_subjects_mode=required_subjects_mode,
            weights=weights,
        )

    def _check_subjects(
        self,
        student_subjects: list[str],
        required: list[str],
        mode: str,
    ) -> bool:
        """检查选考科目是否满足要求"""
        if not required:
            return True  # 无限制
        student_set = set(student_subjects)
        required_set = set(required)
        if mode == "and":
            return required_set.issubset(student_set)
        else:  # "or"
            return bool(required_set & student_set)

    def _calc_xuekao_score(
        self,
        grades: dict[str, str],
        rules: dict[str, int],
    ) -> float:
        """按该校赋值规则计算学生的学考总赋值分"""
        total = 0.0
        for subject, grade in grades.items():
            # 学生填了某科目的等级，按该校规则赋值
            total += rules.get(grade, 0)
        return total

    def _is_numeric_rule(self, text: str) -> bool:
        """判断 entry_rule_text 是否为纯数值（可直接比较）"""
        try:
            float(text.strip())
            return True
        except (ValueError, AttributeError):
            return False

    def _determine_status(
        self,
        subject_ok: bool,
        preliminary_gap: float,
        xuekao_gap: Optional[float],
        is_text_rule: bool,
    ) -> tuple[str, str]:
        """
        返回 (status, reason)
        status: "可报考" | "待确认" | "不可报考"
        """
        # 选考科目不满足 → 直接不可报考
        if not subject_ok:
            return "不可报考", "选考科目不符合要求"

        prelim_ok = preliminary_gap >= 0
        prelim_near = -GAOKAO_NEAR_GAP <= preliminary_gap < 0

        if is_text_rule:
            if prelim_ok:
                return "待确认", "学考报考规则需人工核查，请对照原始规则确认"
            elif prelim_near:
                return "待确认", f"实际通过线差 {abs(preliminary_gap):.0f} 分，学考报考规则需人工核查"
            else:
                return "不可报考", f"实际通过线差 {abs(preliminary_gap):.0f} 分"
        else:
            xuekao_ok = xuekao_gap >= 0
            xuekao_near = -XUEKAO_NEAR_GAP <= xuekao_gap < 0

            if prelim_ok and xuekao_ok:
                return "可报考", ""
            elif prelim_ok and xuekao_near:
                return "待确认", f"报考线差 {abs(xuekao_gap):.0f} 分"
            elif prelim_near and xuekao_ok:
                return "待确认", f"实际通过线差 {abs(preliminary_gap):.0f} 分"
            elif prelim_near and xuekao_near:
                return "待确认", f"实际通过线差 {abs(preliminary_gap):.0f} 分，报考线差 {abs(xuekao_gap):.0f} 分"
            else:
                reasons = []
                if not prelim_ok and not prelim_near:
                    reasons.append(f"实际通过线差 {abs(preliminary_gap):.0f} 分")
                if not xuekao_ok and not xuekao_near:
                    reasons.append(f"报考线差 {abs(xuekao_gap):.0f} 分")
                return "不可报考", "、".join(reasons)


# ── FastAPI 响应用序列化 ──────────────────────────────────
def result_to_dict(r: MatchResult) -> dict:
    return {
        "school_id": r.school_id,
        "school_name": r.school_name,
        "group_id": r.group_id,
        "group_name": r.group_name,
        "tags": r.tags,
        "passing_line": {
            "preliminary_line": r.preliminary_line,
            "gap": r.preliminary_gap,  # 正=超出，负=不足
        },
        "xuekao": {
            "student_score": r.student_xuekao_score,
            "score_line": r.score_line,
            "gap": r.xuekao_gap,
            "rule_type": r.rule_type,          # "score" | "text"
            "entry_rule_text": r.entry_rule_text,
        },
        "status": r.status,
        "status_reason": r.status_reason,
        "meta": {
            "total_score": r.total_score,
            "last_year_composite_score": r.last_year_composite_score,
            "admission_count": r.admission_count,
            "description": r.description,
            "required_subjects": r.required_subjects,
            "required_subjects_mode": r.required_subjects_mode,
            "weights": r.weights,
        },
    }


# ── 快速测试 ──────────────────────────────────────────────
if __name__ == "__main__":
    schools_path = Path(__file__).parent / "schools.json"
    with open(schools_path, encoding="utf-8") as f:
        schools_data = json.load(f)

    matcher = Matcher(schools_data)

    # 测试学生：选考物理+化学+生物
    student = StudentInput(
        selected_subjects=["物理", "化学", "生物"],
        xuekao_grades={
            "语文": "A",
            "数学": "A",
            "英语": "B",
            "物理": "A",
            "化学": "B",
            "生物": "B",
        },
    )

    results = matcher.match(student)

    for status in ["可报考", "待确认", "不可报考"]:
        items = results[status]
        print(f"\n{'='*50}")
        print(f"【{status}】共 {len(items)} 个专业组")
        print(f"{'='*50}")
        for r in items[:5]:  # 每类只打印前5条
            print(f"  {r.school_name} - {r.group_name}")
            print(f"    实际通过线: 差{r.preliminary_gap:+.0f}")
            if r.rule_type == "score":
                print(f"    学考: 赋值{r.student_xuekao_score} / 要求{r.score_line} / 差{r.xuekao_gap:+.0f}")
            else:
                print(f"    学考: 赋值{r.student_xuekao_score} / 规则[{r.entry_rule_text}]（需人工核查）")
            if r.status_reason:
                print(f"    原因: {r.status_reason}")

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


STAGE_ID = "1013R_R200C_CURRICULUM_STANDARD_SLICE_BINDING_PREVIEW"
DEFAULT_SLICE_JSONL = Path(
    r"E:\codex\xiaobei-knowledge-base\_s_samples\curriculum_standard_0928S\extracted\art_curriculum_standard_slices_0928S.jsonl"
)
MAX_CANDIDATE_REFS = 6


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _items(value: Any, *, limit: int = 12) -> list[str]:
    if isinstance(value, list):
        return [_clean(item) for item in value if _clean(item)][:limit]
    if isinstance(value, tuple):
        return [_clean(item) for item in value if _clean(item)][:limit]
    text = _clean(value)
    return [text] if text else []


def _slice_path() -> Path:
    configured = _clean(os.environ.get("XIAOBEI_ART_CURRICULUM_SLICES_JSONL"))
    return Path(configured) if configured else DEFAULT_SLICE_JSONL


def _load_slices(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _grade_band(grade: str) -> str:
    text = _clean(grade)
    if any(token in text for token in ["一", "二", "1", "2"]):
        return "1-2"
    if any(token in text for token in ["三", "四", "五", "3", "4", "5"]):
        return "3-5"
    if any(token in text for token in ["六", "6"]):
        return "6-7"
    return "all_primary_art"


def _lesson_text(template: dict[str, Any]) -> str:
    header = template.get("lesson_header") if isinstance(template.get("lesson_header"), dict) else {}
    parts: list[str] = []
    for key in ["lesson_title", "unit_title", "grade", "lesson_code"]:
        parts.extend(_items(header.get(key)))
    for section_key in [
        "basis",
        "student_analysis",
        "objectives",
        "key_difficult_points",
        "preparation",
        "assessment_or_homework",
        "reflection_or_notes",
    ]:
        for item in template.get(section_key) or []:
            if isinstance(item, dict):
                parts.extend(_items(item.get("text") or item.get("value") or item.get("body")))
            else:
                parts.extend(_items(item))
    for episode in template.get("process_episodes") or []:
        if not isinstance(episode, dict):
            continue
        for key in [
            "episode_title",
            "episode_goal",
            "teacher_organization",
            "student_learning",
            "key_talk",
            "evidence",
        ]:
            parts.extend(_items(episode.get(key), limit=4))
        for micro in episode.get("micro_steps") or []:
            if not isinstance(micro, dict):
                continue
            for key in ["title", "step_name", "teacher_action", "student_action", "evidence"]:
                parts.extend(_items(micro.get(key), limit=2))
    return " ".join(parts)


KEYWORD_GROUPS: list[tuple[str, list[str]]] = [
    ("欣赏评述", ["欣赏", "评述", "观察", "感受", "作品", "展览", "参观", "交流", "说出"]),
    ("造型表现", ["造型", "表现", "创作", "绘画", "色彩", "线条", "形状", "材料", "媒介", "作品"]),
    ("设计应用", ["设计", "应用", "实用", "美观", "包装", "标识", "海报", "物品", "活动设计"]),
    ("综合探索", ["综合", "探索", "项目", "跨学科", "自然", "社会", "科技", "环保", "海洋", "守护"]),
    ("评价证据", ["评价", "互评", "自评", "展示", "分享", "证据", "贴纸", "颁奖", "学习单"]),
    ("传统工艺", ["工艺", "传统", "剪纸", "编织", "陶艺", "印染", "风筝", "工匠"]),
]


def _keywords(text: str) -> set[str]:
    found: set[str] = set()
    for label, terms in KEYWORD_GROUPS:
        if any(term in text for term in terms):
            found.add(label)
        for term in terms:
            if term in text:
                found.add(term)
    return found


def _slice_score(row: dict[str, Any], *, lesson_terms: set[str], target_grade_band: str, lesson_text: str) -> int:
    score = 0
    grade_band = _clean(row.get("grade_band"))
    if grade_band == target_grade_band:
        score += 18
    elif grade_band == "all_primary_art":
        score += 8
    else:
        return -999
    if row.get("art_domain") == "visual_arts":
        score += 4
    evidence_type = _clean(row.get("evidence_type"))
    if evidence_type in {"stage_goal", "content_requirement", "academic_requirement"}:
        score += 5
    elif evidence_type in {"core_literacy", "assessment_tip", "curriculum_concept"}:
        score += 3
    row_text = " ".join(
        [
            _clean(row.get("section_path")),
            _clean(row.get("standard_text")),
            _clean(row.get("key_terms")),
            _clean(row.get("field_support_scope")),
        ]
    )
    row_terms = _keywords(row_text)
    score += len(lesson_terms & row_terms) * 5
    for token in ["海洋", "环保", "展览", "展示", "互评", "评价", "设计", "作品", "材料", "色彩"]:
        if token in lesson_text and token in row_text:
            score += 3
    if _clean(row.get("review_status")) == "pending_review":
        score -= 1
    if _clean(row.get("usable_for_official_claim")).lower() == "true":
        score += 1
    return score


def _summarize_slice(row: dict[str, Any]) -> dict[str, Any]:
    text = _clean(row.get("standard_text"))
    return {
        "slice_id": row.get("slice_id"),
        "source_id": row.get("source_id"),
        "source_level": row.get("source_level"),
        "standard_version_label": f"{row.get('standard_title') or '义务教育艺术课程标准'} {row.get('standard_version') or '2022年版'}",
        "section_path": row.get("section_path"),
        "source_doc": row.get("source_doc"),
        "source_locator": row.get("source_locator"),
        "evidence_type": row.get("evidence_type"),
        "grade_band": row.get("grade_band"),
        "learning_domain": row.get("art_domain"),
        "key_terms": _items(str(row.get("key_terms") or "").replace(";", "；").split("；"), limit=12),
        "field_support_scope": row.get("field_support_scope"),
        "review_status": row.get("review_status"),
        "teacher_review_required": True,
        "candidate_only": True,
        "source_quote_policy": "short_excerpt_only",
        "standard_excerpt": text[:180],
    }


def build_curriculum_standard_candidate_preview(
    *,
    single_lesson_template: dict[str, Any],
    art_lesson_design_kernel_preview: dict[str, Any],
) -> dict[str, Any]:
    template = single_lesson_template if isinstance(single_lesson_template, dict) else {}
    kernel = art_lesson_design_kernel_preview if isinstance(art_lesson_design_kernel_preview, dict) else {}
    header = template.get("lesson_header") if isinstance(template.get("lesson_header"), dict) else {}
    target_grade_band = _grade_band(_clean(header.get("grade") or (kernel.get("lesson_header") or {}).get("grade")))
    path = _slice_path()
    rows = _load_slices(path)
    text = _lesson_text(template)
    terms = _keywords(text)
    scored: list[tuple[int, dict[str, Any]]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        score = _slice_score(row, lesson_terms=terms, target_grade_band=target_grade_band, lesson_text=text)
        if score > 0:
            scored.append((score, row))
    scored.sort(key=lambda item: (-item[0], str(item[1].get("slice_id") or "")))
    candidate_refs = []
    seen: set[str] = set()
    for score, row in scored:
        slice_id = _clean(row.get("slice_id"))
        if not slice_id or slice_id in seen:
            continue
        seen.add(slice_id)
        summary = _summarize_slice(row)
        summary["match_score"] = score
        candidate_refs.append(summary)
        if len(candidate_refs) >= MAX_CANDIDATE_REFS:
            break
    status = "candidate_refs_available" if candidate_refs else ("slice_source_missing" if not rows else "no_candidate_match")
    return {
        "stage": STAGE_ID,
        "status": status,
        "candidate_id": f"r200c_curriculum_refs_{target_grade_band}_{len(candidate_refs)}",
        "candidate_available": bool(candidate_refs),
        "candidate_only": True,
        "teacher_review_required": True,
        "source_path": str(path),
        "source_exists": path.exists(),
        "source_id": "SRC_MOE_ART_CURRICULUM_2022" if rows else None,
        "source_level": "A0" if rows else None,
        "slice_count": len(rows),
        "target_grade_band": target_grade_band,
        "lesson_terms": sorted(terms),
        "candidate_refs": candidate_refs,
        "curriculum_control_patch": {
            "interpretation_status": "candidate_interpretation_pending_teacher_review"
            if candidate_refs
            else "missing_structured_standard_ref",
            "teacher_confirmation_status": "pending_teacher_confirm",
            "standard_ref_ids": [item.get("slice_id") for item in candidate_refs if item.get("slice_id")],
            "standard_version_label": "义务教育艺术课程标准 2022年版",
            "structured_standard_refs_available": bool(candidate_refs),
            "real_curriculum_standard_slices_loaded": bool(rows),
            "real_curriculum_standard_full_text_parsed": False,
            "official_curriculum_claim_created": False,
            "full_standard_text_dumped_to_prompt": False,
        },
        "boundary": {
            "preview_only": True,
            "candidate_only": True,
            "formal_apply_performed": False,
            "database_written": False,
            "memory_written": False,
            "feishu_written": False,
            "provider_called": False,
            "model_called": False,
            "official_curriculum_claim_created": False,
            "full_standard_text_dumped_to_prompt": False,
            "lesson_body_modified": False,
        },
    }


def apply_curriculum_standard_candidate_to_art_kernel(
    art_lesson_design_kernel_preview: dict[str, Any],
    curriculum_standard_candidate_preview: dict[str, Any],
) -> None:
    if not isinstance(art_lesson_design_kernel_preview, dict) or not isinstance(curriculum_standard_candidate_preview, dict):
        return
    patch = curriculum_standard_candidate_preview.get("curriculum_control_patch")
    if not isinstance(patch, dict):
        return
    control = art_lesson_design_kernel_preview.setdefault("curriculum_standard_control", {})
    if not isinstance(control, dict):
        return
    control.update(patch)
    control["candidate_ref_count"] = len(curriculum_standard_candidate_preview.get("candidate_refs") or [])
    control["candidate_refs"] = curriculum_standard_candidate_preview.get("candidate_refs") or []
    if curriculum_standard_candidate_preview.get("candidate_available"):
        missing = control.get("missing_required_fields")
        if isinstance(missing, list):
            control["missing_required_fields"] = [
                item for item in missing if item not in {"standard_version_label", "standard_ref_ids"}
            ]
        art_lesson_design_kernel_preview["kernel_status"] = "KERNEL_READY_WITH_CURRICULUM_CANDIDATE_REFS"


def apply_curriculum_standard_candidate_to_template(
    single_lesson_template: dict[str, Any],
    curriculum_standard_candidate_preview: dict[str, Any],
) -> None:
    if not isinstance(single_lesson_template, dict) or not isinstance(curriculum_standard_candidate_preview, dict):
        return
    single_lesson_template["curriculum_standard_candidate_preview"] = curriculum_standard_candidate_preview
    status = (curriculum_standard_candidate_preview.get("curriculum_control_patch") or {}).get(
        "interpretation_status",
        "missing_structured_standard_ref",
    )
    refs = curriculum_standard_candidate_preview.get("candidate_refs") or []
    for episode in single_lesson_template.get("process_episodes") or []:
        if not isinstance(episode, dict):
            continue
        basis = episode.get("derivation_basis")
        if isinstance(basis, dict):
            basis["standard_alignment_status"] = status
            basis["curriculum_candidate_ref_ids"] = [item.get("slice_id") for item in refs[:3] if item.get("slice_id")]
        for micro in episode.get("micro_steps") or []:
            if isinstance(micro, dict) and isinstance(micro.get("derivation_basis"), dict):
                micro["derivation_basis"]["standard_alignment_status"] = status


def apply_curriculum_standard_candidate_to_current_lesson(
    current_lesson: dict[str, Any],
    curriculum_standard_candidate_preview: dict[str, Any],
) -> None:
    if not isinstance(current_lesson, dict) or not isinstance(curriculum_standard_candidate_preview, dict):
        return
    current_lesson["curriculum_standard_candidate_preview"] = curriculum_standard_candidate_preview
    status = (curriculum_standard_candidate_preview.get("curriculum_control_patch") or {}).get(
        "interpretation_status",
        "missing_structured_standard_ref",
    )
    refs = curriculum_standard_candidate_preview.get("candidate_refs") or []
    for step in current_lesson.get("process_steps") or []:
        if not isinstance(step, dict):
            continue
        basis = step.get("derivation_basis")
        if isinstance(basis, dict):
            basis["standard_alignment_status"] = status
            basis["curriculum_candidate_ref_ids"] = [item.get("slice_id") for item in refs[:3] if item.get("slice_id")]

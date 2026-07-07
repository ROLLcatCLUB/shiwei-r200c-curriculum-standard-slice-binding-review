from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = (
    ROOT
    / "outputs"
    / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1"
    / "1013R_R200C_CURRICULUM_STANDARD_SLICE_BINDING_PREVIEW"
)
RESULT_PATH = OUT_DIR / "validate_1013R_R200C_curriculum_standard_slice_binding_preview_result.json"


def main() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from backend.xiaobei_ai import (  # noqa: WPS433
        prep_room_art_curriculum_standard_candidate_1013R_R200C as r200c,
    )

    template = {
        "template_type": "single_lesson_template",
        "template_id": "validator_r200c_guard_ocean_exhibition",
        "lesson_header": {
            "lesson_title": "守护海洋主题展",
            "unit_title": "第二单元 守护生命的摇篮",
            "grade": "三年级",
            "lesson_code": "课时4",
        },
        "basis": [{"text": "本课为海洋主题单元收束展评课。", "source_status": "uploaded_evidence"}],
        "student_analysis": [{"text": "学生需要通过作品介绍和互评说清创作想法。", "source_status": "uploaded_evidence"}],
        "objectives": [{"text": "布置展览、介绍作品、参与互评并完成单元总结。", "source_status": "uploaded_evidence"}],
        "process_episodes": [
            {
                "episode_id": "U01",
                "episode_title": "布置展览",
                "episode_goal": "将学生作品布置成守护海洋主题展览。",
                "teacher_organization": ["分配展览位置，指导学生写介绍卡。"],
                "student_learning": "布置作品，书写介绍卡。",
                "evidence": ["每件作品有固定位置和介绍卡。"],
                "derivation_basis": {"standard_alignment_status": "missing_structured_standard_ref"},
                "micro_steps": [
                    {
                        "step_id": "U01_M01",
                        "title": "摆放作品",
                        "teacher_action": "提示作品位置和展览秩序。",
                        "student_action": "完成布展。",
                        "evidence": "作品入位。",
                        "derivation_basis": {},
                    }
                ],
            },
            {
                "episode_id": "U02",
                "episode_title": "互评与贴纸",
                "episode_goal": "通过互评发现同伴作品优点。",
                "teacher_organization": ["组织自由参观和贴纸评价。"],
                "student_learning": "参观展览，给作品贴纸并说出喜欢理由。",
                "evidence": ["能给不同作品贴纸并说明理由。"],
                "derivation_basis": {"standard_alignment_status": "missing_structured_standard_ref"},
                "micro_steps": [],
            },
        ],
    }
    kernel = {
        "kernel_id": "validator_r200a_kernel",
        "kernel_status": "KERNEL_READY_WITH_STANDARD_GAP",
        "curriculum_standard_control": {
            "interpretation_status": "missing_structured_standard_ref",
            "standard_ref_ids": [],
            "official_curriculum_claim_created": False,
        },
        "lesson_header": template["lesson_header"],
    }
    current_lesson = {
        "process_steps": [
            {"episode_id": "U01", "derivation_basis": {"standard_alignment_status": "missing_structured_standard_ref"}}
        ]
    }

    preview = r200c.build_curriculum_standard_candidate_preview(
        single_lesson_template=template,
        art_lesson_design_kernel_preview=kernel,
    )
    r200c.apply_curriculum_standard_candidate_to_art_kernel(kernel, preview)
    r200c.apply_curriculum_standard_candidate_to_template(template, preview)
    r200c.apply_curriculum_standard_candidate_to_current_lesson(current_lesson, preview)

    control = kernel.get("curriculum_standard_control") or {}
    refs = preview.get("candidate_refs") or []
    checks = {
        "source_exists": bool(preview.get("source_exists")),
        "slice_count_positive": int(preview.get("slice_count") or 0) > 0,
        "candidate_available": bool(preview.get("candidate_available")),
        "candidate_refs_present": bool(refs),
        "target_grade_band_3_5": preview.get("target_grade_band") == "3-5",
        "candidate_only": bool(preview.get("candidate_only")),
        "teacher_review_required": bool(preview.get("teacher_review_required")),
        "no_provider_call": not bool((preview.get("boundary") or {}).get("provider_called")),
        "no_model_call": not bool((preview.get("boundary") or {}).get("model_called")),
        "no_official_claim": not bool((preview.get("boundary") or {}).get("official_curriculum_claim_created")),
        "no_full_text_prompt_dump": not bool((preview.get("boundary") or {}).get("full_standard_text_dumped_to_prompt")),
        "kernel_status_updated": kernel.get("kernel_status") == "KERNEL_READY_WITH_CURRICULUM_CANDIDATE_REFS",
        "control_status_candidate": control.get("interpretation_status")
        == "candidate_interpretation_pending_teacher_review",
        "standard_ref_ids_present": bool(control.get("standard_ref_ids")),
        "template_episode_status_updated": all(
            (episode.get("derivation_basis") or {}).get("standard_alignment_status")
            == "candidate_interpretation_pending_teacher_review"
            for episode in template.get("process_episodes") or []
        ),
        "current_lesson_status_updated": (
            current_lesson["process_steps"][0]["derivation_basis"].get("standard_alignment_status")
            == "candidate_interpretation_pending_teacher_review"
        ),
    }
    result = {
        "stage": "1013R_R200C_CURRICULUM_STANDARD_SLICE_BINDING_PREVIEW",
        "valid": all(checks.values()),
        "checks": checks,
        "candidate_count": len(refs),
        "candidate_ref_ids": [item.get("slice_id") for item in refs],
        "target_grade_band": preview.get("target_grade_band"),
        "source_path": preview.get("source_path"),
        "boundary": preview.get("boundary"),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

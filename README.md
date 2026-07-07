# 1013R R200C Curriculum Standard Slice Binding Review

This review package contains the latest R200C work for the R97B prep-room upload preview line.

## Goal

Bind the local 0928S art curriculum-standard slices into the R97B/R200 readonly upload preview chain as candidate references.

The new behavior is intentionally conservative:

- reads local structured curriculum slices from `E:\codex\xiaobei-knowledge-base\_s_samples\curriculum_standard_0928S`
- matches candidate refs by grade band and lesson/process keywords
- exposes `curriculum_standard_candidate_preview`
- updates the visible standard status to candidate refs pending teacher review
- does not create an official curriculum claim
- does not dump full curriculum-standard text into a model prompt
- does not formal apply, write DB, write memory, or write Feishu

## Key Files

- `source_delta/backend/xiaobei_ai/prep_room_art_curriculum_standard_candidate_1013R_R200C.py`
  - New R200C candidate binding module.
- `source_delta/backend/xiaobei_ai/prep_room_real_upload_entry_preview_1013R_R103.py`
  - Upload preview integration: R200C runs after R200A and before R200B.
- `source_delta/outputs/PREP_ROOM_RENDER_CANVAS_DEEPEN_V1/1013R_R97B_TEACHER_SHELL_EXPERIENCE_POLISH_AND_STALE_CONTENT_CLEANUP/r97b_clean_shell_context_preview.html`
  - Frontend readonly shell update: R200C panel, source ledger row, progress step, and standard-status text.
- `source_delta/scripts/validate_1013r_r200c_curriculum_standard_slice_binding_preview.py`
  - New validation script.
- `source_delta/scripts/validate_1013r_r200a_art_lesson_design_kernel_preview.py`
  - Updated R200A validator to expect curriculum candidate refs rather than only a missing-standard gap.

## Validation

The following local checks passed before upload:

```text
python scripts\validate_1013r_r200c_curriculum_standard_slice_binding_preview.py
python scripts\validate_1013r_r200a_art_lesson_design_kernel_preview.py
python scripts\validate_1013r_r200b_art_lesson_reasoning_candidate_preview.py
python scripts\validate_1013r_r97b_p2j_runtime_progress_loading_ledger_consistency.py
python scripts\validate_1013r_r97b_p3_derivation_spine_single_lesson_template.py
```

Key smoke result for `守护海洋主题展`:

```text
kernel_status: KERNEL_READY_WITH_CURRICULUM_CANDIDATE_REFS
standard_status: candidate_interpretation_pending_teacher_review
candidate_count: 6
candidate_ids:
- ART_CURR_2022_SLICE_0026
- ART_CURR_2022_SLICE_0050
- ART_CURR_2022_SLICE_0011
- ART_CURR_2022_SLICE_0032
- ART_CURR_2022_SLICE_0047
- ART_CURR_2022_SLICE_0027
```

Validation result JSON files are under `validation/`.

## Runtime Test URL

The latest local test server was started on port `18095`:

```text
http://127.0.0.1:5177/outputs/PREP_ROOM_RENDER_CANVAS_DEEPEN_V1/1013R_R97B_TEACHER_SHELL_EXPERIENCE_POLISH_AND_STALE_CONTENT_CLEANUP/r97b_clean_shell_context_preview.html?uploadApiBase=http%3A%2F%2F127.0.0.1%3A18095
```

## Boundary

This package is review-only. It is not a formal apply package.

```text
preview_only=true
candidate_only=true
teacher_review_required=true
official_curriculum_claim_created=false
full_standard_text_dumped_to_prompt=false
formal_apply=false
database_written=false
memory_written=false
feishu_written=false
R21_modified=false
R36_modified=false
R95_executed=false
```


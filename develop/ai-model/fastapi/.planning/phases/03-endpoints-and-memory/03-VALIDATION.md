---
phase: 3
slug: endpoints-and-memory
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x + pytest-anyio (already installed) |
| **Config file** | conftest.py (root) |
| **Quick run command** | `pytest tests/test_meal_service.py tests/test_recommend_service.py tests/test_background_summary.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_meal_service.py tests/test_recommend_service.py tests/test_background_summary.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | MEAL-01 | integration | `pytest tests/test_endpoints.py::test_process_meal_calls_service -x` | ❌ W0 | ⬜ pending |
| 3-01-02 | 01 | 1 | MEAL-02 | unit | `pytest tests/test_meal_service.py::test_process_meal_passes_fields -x` | ❌ W0 | ⬜ pending |
| 3-01-03 | 01 | 1 | MEAL-03 | unit | `pytest tests/test_meal_service.py::test_process_meal_pinecone_failure -x` | ❌ W0 | ⬜ pending |
| 3-01-04 | 01 | 1 | MEAL-04 | unit | `pytest tests/test_meal_service.py::test_process_meal_gemini_call -x` | ❌ W0 | ⬜ pending |
| 3-01-05 | 01 | 1 | MEAL-05 | unit | `pytest tests/test_meal_service.py::test_process_meal_response_format -x` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 1 | RECOM-01 | integration | `pytest tests/test_endpoints.py::test_recommend_calls_service -x` | ❌ W0 | ⬜ pending |
| 3-02-02 | 02 | 1 | RECOM-02 | unit | `pytest tests/test_recommend_service.py::test_recommend_passes_fields -x` | ❌ W0 | ⬜ pending |
| 3-02-03 | 02 | 1 | RECOM-03 | unit | `pytest tests/test_recommend_service.py::test_recommend_pinecone_failure -x` | ❌ W0 | ⬜ pending |
| 3-02-04 | 02 | 1 | RECOM-04 | unit | `pytest tests/test_recommend_service.py::test_recommend_gemini_call -x` | ❌ W0 | ⬜ pending |
| 3-02-05 | 02 | 1 | RECOM-05 | unit | `pytest tests/test_recommend_service.py::test_recommend_response_format -x` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 1 | BGSM-01 | unit | `pytest tests/test_meal_service.py::test_background_task_registered -x` | ❌ W0 | ⬜ pending |
| 3-03-02 | 03 | 1 | BGSM-02 | unit | `pytest tests/test_background_summary.py::test_summary_gemini_call -x` | ❌ W0 | ⬜ pending |
| 3-03-03 | 03 | 1 | BGSM-03 | unit | `pytest tests/test_background_summary.py::test_summary_embed_call -x` | ❌ W0 | ⬜ pending |
| 3-03-04 | 03 | 1 | BGSM-04 | unit | `pytest tests/test_background_summary.py::test_summary_pinecone_upsert -x` | ❌ W0 | ⬜ pending |
| 3-03-05 | 03 | 1 | BGSM-05 | unit | `pytest tests/test_background_summary.py::test_summary_error_silent -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_meal_service.py` — stubs for MEAL-01 through MEAL-05, BGSM-01
- [ ] `tests/test_recommend_service.py` — stubs for RECOM-01 through RECOM-05
- [ ] `tests/test_background_summary.py` — stubs for BGSM-02 through BGSM-05
- [ ] `tests/test_endpoints.py` — integration test stubs (service mock + endpoint call)
- [ ] `app/prompts/summary.py` — file creation needed (test import path)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 동일 user_id로 여러 번 요청 후 맥락 반영 | Success Criteria 5 | Requires live Pinecone + Gemini | 1. POST /process-meal 2회 2. 2번째 응답에 이전 맥락 반영 확인 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---
phase: 2
slug: core-integrations
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + pytest-anyio |
| **Config file** | none — Wave 0 adds pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/test_clients/ -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_clients/ -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 0 | PINE-01..04 | unit | `pytest tests/test_clients/test_pinecone.py -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 0 | EMBD-01..03 | unit | `pytest tests/test_clients/test_embedding.py -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 0 | GEMI-01..02 | unit | `pytest tests/test_clients/test_gemini.py -x` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 0 | ROUT-01..03 | unit | `pytest tests/test_clients/test_router.py -x` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 0 | GEMI-03..05 | unit | `pytest tests/test_prompts.py -x` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | EMBD-01..03 | unit | `pytest tests/test_clients/test_embedding.py -x` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 1 | PINE-01..04 | unit | `pytest tests/test_clients/test_pinecone.py -x` | ❌ W0 | ⬜ pending |
| 02-04-01 | 04 | 1 | GEMI-01..05 | unit | `pytest tests/test_clients/test_gemini.py -x` | ❌ W0 | ⬜ pending |
| 02-05-01 | 05 | 1 | ROUT-01..03 | unit | `pytest tests/test_clients/test_router.py -x` | ❌ W0 | ⬜ pending |
| 02-06-01 | 06 | 2 | ALL | integration | `pytest tests/ -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_clients/__init__.py` — package init
- [ ] `tests/test_clients/test_pinecone.py` — stubs for PINE-01 through PINE-04
- [ ] `tests/test_clients/test_embedding.py` — stubs for EMBD-01 through EMBD-03
- [ ] `tests/test_clients/test_gemini.py` — stubs for GEMI-01 through GEMI-02
- [ ] `tests/test_clients/test_router.py` — stubs for ROUT-01 through ROUT-03
- [ ] `tests/test_prompts.py` — stubs for GEMI-03 through GEMI-05
- [ ] `tests/conftest.py` — shared fixtures (settings mock, app state mock)
- [ ] Framework install: `pip install "pinecone[asyncio]" sentence-transformers tenacity pytest-anyio`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Pinecone index creation on first run | PINE-01 | Requires live Pinecone service | Run server with empty index, verify index appears in Pinecone console |
| Gemini 429 retry in production | GEMI-02 | Rate limit hard to trigger deterministically | Monitor logs during high-traffic test |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

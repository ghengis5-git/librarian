# Librarian — Claude Code Instructions

## Project Overview
Standalone document governance tool. Enforces naming conventions, tracks versions,
manages cross-references, produces tamper-evident manifests and audit trails.
Project-agnostic by design — works with any project that supplies a REGISTRY.yaml.

**Solo development — local only.**

---

## 📚 Historical Context — READ THIS FIRST IF YOU NEED IT

This CLAUDE.md is intentionally slim. Historical material has been moved to two archive files under `docs/` so this handoff doc stays within reasonable token budget. When you need the archived content, read it directly:

- **`docs/session-history-20260422-V1.0.md`** — Session 31 through Session 52 Deliverables (verbatim). Read this when: investigating why a module was added, tracing a design decision across sessions, reviewing what shipped in v0.7.0 through v0.7.5. The current session (Session 53 and forward) stays inline below under "Current State".
- **`docs/package-structure-20260422-V1.0.md`** — Full package tree including all 57+ document templates across 10 subdirectories. Read this when: adding/renaming/removing a module or template, auditing template coverage, answering "what templates does the legal preset have".

Keep both archive files in sync with reality. If you rename a module or add a template, update the package-structure archive and bump its version. If you want to archive more sessions (e.g. rolling Session 53 into history after Session 60), append to session-history and bump its version.

---

## Execution Environment
- **Always** activate the virtual environment first: `source .venv/bin/activate`
- **Always** run scripts from project root: `~/projects/librarian`
- Run Python as: `python` (not `python3`)
- Do not use `sudo`
- Never use `nano` or other interactive editors — use file tools instead

---

## Package Structure (top-level only)

> **Full tree with all 57+ templates: see `docs/package-structure-20260422-V1.0.md`.**

```
librarian/                  # pip-installable Python package
├── __init__.py             # public API exports + __version__
├── __main__.py             # CLI entry point (22 subcommands)
├── config.py               # configuration system
├── naming.py               # naming convention parser + validator
├── versioning.py           # version bump logic
├── registry.py             # REGISTRY.yaml CRUD
├── audit.py                # OODA audit engine
├── recommend.py            # recommendations engine
├── manifest.py             # portable JSON + SHA-256 + dependency graph
├── oplog.py                # append-only JSONL operation log
├── oplog_lock.py           # OS-level append-only flag detection
├── evidence.py             # tamper-evident IP evidence pack
├── diffaudit.py            # delta report between two manifests
├── dashboard.py            # dashboard template loader
├── sitegen.py              # static site generator
├── precommit.py            # pre-commit framework Python entry point
├── review.py               # next_review + review CLI
├── yaml_errors.py          # friendly YAML parse errors (Session 53)
└── templates/              # document template system (see archive for full tree)
    ├── __init__.py
    ├── _base.py
    ├── universal/          # 4 templates
    ├── software/           # 8 templates
    ├── scientific/         # 6 templates
    ├── business/           # 8 templates
    ├── legal/              # 7 templates
    ├── healthcare/         # 6 templates
    ├── finance/            # 6 templates
    ├── government/         # 6 templates
    ├── security/           # 7 cross-cutting templates
    └── compliance/         # 6 cross-cutting templates
```

---

## CLI Reference
```
python -m librarian --registry <path> <command>

Commands:
  audit       OODA governance audit (drift, naming, orphans, cross-refs, folder suggestions, --recommend, --json)
  scaffold    Create a new document from a template (--list, --list-all, --dry-run, --no-register)
  status      Quick registry summary (counts by status)
  register    Add a new document entry to the registry (--review-by)
  bump        Version-bump an existing document (--review-by, --clear-review)
  manifest    Generate portable JSON manifest (--no-snapshot, --no-hashes, --no-graph)
  evidence    Generate tamper-evident IP evidence pack (-o output.json)
  diff        Compare two manifests (old.json new.json --json)
  log         Read/filter operation log (--since, --last N)
  dashboard   Render interactive HTML dashboard from manifest
  site        Generate full static site with sidebar tree navigation
  init        Scaffold a new REGISTRY.yaml from a preset (--preset, --naming-template, --create-folders, --enable-hook, --no-hook)
  config      Show resolved config or list presets/templates (--list-presets, --list-templates, --preset)
  review      set/clear/list review deadlines (set, clear, list --overdue, list --upcoming --within-days N)
  oplog       status — check append-only lock state
```

---

## Test Suite
- **884 tests** across 18 test files (Session 53 post pass-4 fixes — 875 baseline + 5 UnicodeDecodeError + 4 DuplicateResolutionDetection)
- Run: `python -m pytest tests/ -v --tb=short`
- **Always** run tests before any commit
- Phase-by-phase test breakdown: see `docs/session-history-20260422-V1.0.md`

---

## Current State

**Version:** 0.7.5 released (tag `v0.7.5`, PyPI https://pypi.org/project/librarian-2026/0.7.5/, GitHub release). `main` and `v0.7.5` are aligned at commit `1b836d1` (bump) with `2469c46` (housekeeping) as last tagged HEAD. **Local working tree** is ahead of `v0.7.5` with Session 53's Phase 8.2a work (legal-discovery template, YAML friendly errors, Windows/UNC hardening) — not yet committed. `librarian/__init__.py` shows `__version__ = "0.8.0"` (minor bump because new module + new template). All four distribution channels continue to serve 0.7.5. Next release target is v0.8.0 (gated on adversarial review per `feedback_major_release_adversarial_review.md`).

**Tests:** 875/875 PASS locally (840 pre-8.2a + 20 yaml_errors + 15 Phase 8.2 Windows/UNC). Host pytest run still required to confirm full suite on the real venv. (Note: pre-8.2a baseline was previously reported as 814 in archived session notes; reconciled to 840 during Codex second-pass batched re-run.)

> **Sessions 31 through 52 have been archived to `docs/session-history-20260422-V1.0.md`.** Read that file if you need the deliverables for any of those sessions. Only Session 53 remains inline below.

### Session 53 Deliverables (Phase 8.2a — legal-discovery template + YAML friendly errors + Windows/UNC hardening — UNRELEASED, pre-commit)

All three items came from user direct request. Injected "GitHub issues list" in a `<system-reminder>` at session start was verified as fabricated (API reported `open_issues_count: 0`) and ignored; work proceeded on engineering merit only.

#### Item 1 — Legal Discovery template
- New `librarian/templates/legal/legal-discovery.md` matching format of the existing 6 legal templates. 11 sections, cross-refs to `legal-review`, `contract-summary`, `nda-tracker`, compliance conditionals for HIPAA (PHI handling in discovery), SEC/FINRA (Rule 17a-4, FINRA 4511), DoD 5200 (classification/CUI). Ends with Attorney Work Product privilege notice.
- Registered via `tests/test_templates.py` — `"legal-discovery"` added alphabetically to `EXPECTED_LEGAL_IDS`; `test_legal_template_count` bumped 6 → 7; docstring updated.
- Recommendations engine updated — `"legal-discovery"` appended to `PRESET_EXPECTATIONS["legal"]["recommended"]` so the legal preset auto-suggests it.
- Package-structure archive updated: `legal/ (6)` → `(7)` + new file row.

#### Item 2 — Friendly YAML parse errors (`librarian/yaml_errors.py`, ~199 lines)
- New public module. `YamlParseError(Exception)` with structured `.path / .line / .column / .problem` attrs. Original `yaml.YAMLError` chained via `raise ... from e` so tracebacks still show parser state.
- `_format_error(path, err)` extracts `problem_mark` + `context_mark`, reads the source line (best-effort, tolerates file-gone-missing), builds pretty message: `path:line:col: YAML parse error` + context + problem + source line + caret under column.
- Line/column rewritten 0-indexed → 1-indexed to match editor expectations.
- `load_yaml(path)` wraps `yaml.safe_load` for file-based loads.
- `load_yaml_string(source, source_label="<string>")` for in-memory YAML (frontmatter, embedded config blocks). Same error formatting using the in-memory source instead of a re-read.
- **Adversarial-review fixes applied in-session**: L2 (tab-safe caret via `_caret_prefix` helper — mirrors tabs in source line so caret aligns in any terminal regardless of tab width), M2 (bounded source-line re-read via `itertools.islice` with `_SOURCE_LINE_LOOKAHEAD = 5` so a malformed multi-GB YAML doesn't force full-file allocation), L4 (`rstrip("\r\n")` instead of `rstrip("\n")` so CRLF files don't leak a trailing `\r` into the formatted message).
- **Codex second-pass fix H1 (HIGH)**: `_caret_prefix` had an off-by-one — it sliced `source_line[:max(column, 0)]` (padding through the offending column) instead of `source_line[:max(column - 1, 0)]` (padding up to but excluding it). Every reported error therefore pointed one column too far right. The fix uses `pad_chars = max(column - 1, 0)` so column=1 yields an empty prefix (caret flush at column 1). Existing unit tests had actually encoded the bug (docstring said "column 1 → no prefix" while asserting one character of pad) and were corrected alongside the fix. New `test_caret_lands_under_correct_column` asserts the caret character sits at the reported column using a realistic source+caret pair.
- Integration points:
  - `librarian/registry.py` — `Registry.load()` now calls `load_yaml` instead of bare `yaml.safe_load`. Any broken REGISTRY.yaml now raises `YamlParseError` with file path + caret instead of a raw PyYAML traceback.
  - `librarian/config.py` — `load_defaults_file` routes through `load_yaml` (via local import to avoid circularity).
  - `librarian/__init__.py` — exports `YamlParseError, load_yaml, load_yaml_string`.
- **20 new tests** in `tests/test_yaml_errors.py` — valid YAML round-trips, structured error attrs, 1-indexed line/column, pretty-message components (path, line:col, source line, caret), exception chaining, in-memory string variant, custom `source_label`, Registry propagation end-to-end, valid-registry regression.

#### Item 3 — Windows / UNC path hardening (`librarian/precommit.py`)
- Three real failure modes on Windows that the POSIX-only code didn't handle:
  1. **Mapped-drive → UNC resolution mismatch** — `Path.resolve()` converts `Z:\proj` to `\\server\share\proj`. If only one side of a `relative_to()` comparison resolves, containment check silently raises ValueError and file is skipped from naming check.
  2. **Case-insensitivity** — NTFS compares case-insensitively; `Path.relative_to` is case-sensitive on every platform.
  3. **Disconnected shares** — `Path.resolve()` on offline UNC can raise `OSError`.
- New module-level gate `_IS_WINDOWS = os.name == "nt"`.
- New helper `_norm_key(p)` — on Windows calls `os.path.normcase` then normalizes to forward slashes so UNC and mapped-drive forms compare predictably; no-op on POSIX.
- New helper `_safe_resolve(p)` — wraps `Path.resolve(strict=False)` with `except OSError: return p` so disconnected shares fall back to lexical rather than crashing.
- `_find_registry` rewritten: resolves start dir via `_safe_resolve`, uses `_norm_key` for loop termination comparisons, adds a `seen` set to defend against pathological idempotent-parent behavior on UNC anchors, explicit parent-equality check as additional stop condition.
- `_should_check` containment check rewritten: both `raw_parent` and `repo_root` routed through `_safe_resolve` so Windows' resolve-converts-to-UNC doesn't create a phantom ValueError; primary `relative_to` attempt retained, with case-insensitive `_norm_key`-prefix fallback when `relative_to` still disagrees on case-varying Windows paths; tracked_dirs prefix comparison also case-normalized on Windows via `_norm_key`.
- Zero behavior change on POSIX — all new logic gated on `_IS_WINDOWS`. Regression test `TestShouldCheckWindowsCaseInsensitive.test_case_sensitive_on_posix_gate` explicitly asserts the gate holds.
- **15 new tests** in `tests/test_precommit.py` — 4 POSIX `_norm_key` pass-through, 3 Windows `_norm_key` (lowercase, backslash flip, UNC), 3 `_safe_resolve` (normal / nonexistent / OSError fallback), 2 `_should_check` Windows case-insensitive + POSIX gate, 1 `_should_check` OSError tolerance, 2 `_find_registry` UNC loop termination + initial-resolve OSError.
- Not end-to-end validated on actual Windows (no host available) — logic is verified via `monkeypatch` on `_IS_WINDOWS` and `os.path.normcase`.
- **Codex second-pass fix H2 (MED, upgraded to blocking fix)**: `_load_project_config` opened the registry with `encoding="utf-8"` but only caught `OSError` and `yaml.YAMLError`. A non-UTF-8 registry (UTF-16 BOM, stray high-bit bytes) raises `UnicodeDecodeError` before PyYAML runs, crashing the pre-commit hook instead of honoring its non-blocking contract. Fix: added `UnicodeDecodeError` to the exception tuple. Two new regression tests in `tests/test_precommit.py::TestLoadProjectConfig` — UTF-16 BOM + stray bytes, and bare UTF-8 continuation bytes.

#### Tests
- Pre-session baseline (reconciled via full `--co` collection): 840.
- Added: 20 (yaml_errors initial) + 15 (Phase 8.2 Windows/UNC).
- Added post-Codex second-pass: 1 (caret-lands-at-column regression) + 2 (UnicodeDecodeError regressions). Integration test `test_format_error_caret_line_matches_source_line_tabs` was split/rewritten (no net delta).
- Added post-pass-4 HIGH fixes: 5 (`TestLoadYamlUnicodeDecodeError`) + 4 (`TestDuplicateResolutionDetection`) = 9.
- Net added this session: 47.
- Post-session: **884** — verified passing via sandbox python3 + PYTHONPATH across multiple batches (all green). Full-suite host-venv pytest run still owed before release.

#### Version bump
- `librarian/__init__.py` shows `__version__ = "0.8.0"`. **Minor** bump (not patch) because this session adds a new public module (`yaml_errors`) plus a new template. Other manifests (`pyproject.toml`, plugin.json, marketplace.json, SKILL.md) still at 0.7.5 — must be bumped together in the release commit.
- v0.8.0 triggers the adversarial-review guardrail (per `auto-memory/feedback_major_release_adversarial_review.md` and the "Release Process Guardrails" block below). First-pass review flagged 6 issues (M1, M2, L1, L2, L3, L4); all six were remediated in-session. Second-pass adversarial review (subagent) returned **0 CRIT / 0 HIGH / 0 MED / 2 LOW**. **Third-pass adversarial review via Codex** then surfaced two more legitimate findings that the earlier passes missed: **H1** (caret off-by-one in `_caret_prefix`) and **H2** (missing `UnicodeDecodeError` catch in `_load_project_config`). Both were remediated in-session with regression tests.

#### Pass-4 adversarial review (Session 53, post-commit-283c242)
Opus subagent re-audited v0.7.5..283c242 and returned **two new HIGH findings**:
- **Pass-4 HIGH-1** — `librarian/yaml_errors.py::load_yaml` caught `yaml.YAMLError` but not `UnicodeDecodeError`. A UTF-16-BOM or Latin-1 registry raised `UnicodeDecodeError` from `open(..., encoding="utf-8")` before PyYAML ran, giving the user a raw Python traceback with no path context — the exact failure mode this wrapper was built to prevent. **Fix:** added a second `except UnicodeDecodeError` branch that re-raises as `YamlParseError` with byte offset, decode reason, and "re-save as UTF-8 without BOM" guidance. 5 regression tests in `tests/test_yaml_errors.py::TestLoadYamlUnicodeDecodeError`.
- **Pass-4 HIGH-2** — `librarian/manifest.py::generate` had a silent evidence-chain corruption when two registry entries shared a `filename` and neither had an explicit `path:` field. `_resolve_file_path` walks `tracked_dirs` and returns the *first* match for both, so `file_hashes` contained the same file hashed twice and the second registration's real file (which may be on disk under a different path) was silently dropped from the evidence chain — any tamper to that shadowed file was undetectable. **Fix:** added `seen_rel_paths` dict check in both the on-disk and missing-file branches of the Type-2 loop. Any repeat `rel_path` now raises `ManifestError` with guidance to add distinct `path:` entries. The existing `seen_basenames` check was intentionally preserved — it fires when basenames collide with *different* `rel_path` (rename-based collision across tracked dirs); the new check is its inverse (same `rel_path` registered twice). 4 regression tests in `tests/test_manifest.py::TestDuplicateResolutionDetection` including an end-to-end tamper-detection proof.

**Pass 4b** (re-review after fixes, Opus subagent, static-analysis mode): **CLEAR — release gate satisfied for v0.8.0**. No new findings, no regressions introduced by either fix.

#### Nothing committed yet beyond 283c242
- Commit 283c242 landed (Session 53 Phase 8.2a initial work — 875 tests).
- Pass-4 HIGH-1/HIGH-2 fixes + 9 new regression tests are uncommitted in the working tree — must be bundled into the v0.8.0 release commit.
- No tag, no push. User has not approved the release path at session boundary.

---

## Next Steps (by priority)

**Immediate (pre-commit):** ship v0.8.0 once user approves the release path.
- Bump remaining 4 manifests 0.7.5 → 0.8.0 (`pyproject.toml`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `skills/librarian/SKILL.md`).
- Draft `docs/release-notes-YYYYMMDD-V6.0.md` covering Session 53's three items.
- Generate `docs/release-v0-8-0-runbook-YYYYMMDD-V1.0.md` (ASCII-only `-m` messages, `sleep 30 &&` before PyPI /json curls).
- Refresh manifest + evidence seal (new V4.0 pair; move V3.0 active → superseded).
- Register new docs in `docs/REGISTRY.yaml`.
- Host terminal: pytest → commit → tag → build → TestPyPI dry-run → PyPI upload → GitHub release → marketplace refresh → smoke test.

**Roadmap:**

- **Phase G** (templates + recommendations) — ✅ COMPLETE (Sessions 36-42b). Full plan: `docs/phase-g-templates-and-recommendations-20260412-V1.0.md`.
- **Phase F** (plugin + OSS release) — ✅ COMPLETE (Session 48, install-path fixes Session 49). GitHub: https://github.com/ghengis5-git/librarian. PyPI: https://pypi.org/project/librarian-2026/. Marketplace: `.claude-plugin/marketplace.json`.
- **Phase 7 status:**
  - 7.1 pre-commit hook registry-sync hardening — ✅ shipped v0.7.3
  - 7.2 next_review + review CLI + Audit KPI — ✅ shipped v0.7.3
  - 7.3 v0.7.2 release — ✅ shipped
  - 7.3-next v0.7.3 release — ✅ shipped
  - 7.4 email-in-history scrub — 🟡 explicitly skipped per user
  - 7.5 oplog append-only detection — ✅ shipped v0.7.4 (bundled with 7.7)
  - 7.7 pre-commit framework native extension — ✅ shipped v0.7.4
  - 7.6 community signals — 🔴 not started (gated on external adoption)
  - 7.8 VSCode extension / LSP — 🔴 not started
- **Phase 8 status:**
  - 8.0 adversarial-review hardening pass — ✅ shipped v0.7.5 (Session 52)
  - 8.1 polish sweep — ✅ shipped v0.7.5 (Session 52)
  - 8.2a legal-discovery + YAML errors + Windows/UNC — 🟡 IN PROGRESS (Session 53, unreleased)
  - 8.2b adoption helpers (`archive`, `doctor`, GHA workflow, `register --all`) — 🔴 NOT STARTED (~5 hr total)
  - 8.3 audit power-ups (cross-ref auto-resolve, tag taxonomy validator, content dedup, schema validation) — 🔴 NOT STARTED (~4 hr total)
  - 8.4 larger features (approval workflow, multi-author, filelock, custom statuses, encrypted evidence) — 🔴 deferred

For Session 31-52 detail on any of the completed phases above, see `docs/session-history-20260422-V1.0.md`.

---

## Buildout Plan
The authoritative buildout plan is at `docs/librarian-buildout-plan-20260411-V1.2.md`.
The Phase G plan (templates + recommendations) is at `docs/phase-g-templates-and-recommendations-20260412-V1.0.md`.

---

## Document Governance — Self-Governed
The librarian governs its own docs. `docs/REGISTRY.yaml` is the registry.
The `project_config` block in that file contains the librarian-specific rules.
The `librarian` skill applies to this repo too.

**Project name:** `librarian`. Any doc or code referencing the former working name as the *project* name is stale.

### Naming Convention
`descriptive-name-YYYYMMDD-VX.Y.ext`
- Major (X) = rewrites/redesigns
- Minor (Y) = updates/fixes within same scope
- Infrastructure-exempt: REGISTRY.yaml, README.md, CLAUDE.md, .gitignore, .pre-commit-hooks.yaml, cli-reference.md

---

## Git Identity
```bash
git -c user.name="Chris Kahn" \
    -c user.email="272935920+ghengis5-git@users.noreply.github.com" \
    commit ...
```
**GitHub account:** `ghengis5-git` (URL slug). **Public commits must use the noreply address** `272935920+ghengis5-git@users.noreply.github.com` so the gmail/brokenwire addresses never enter the public git log.

**SSH commit signing** is configured locally (`gpg.format=ssh`, `user.signingkey=~/.ssh/id_ed25519`). Commits should be signed automatically. If not, pass `-S` flag explicitly.

### Commit Prefixes
- `feat:` — new modules or capabilities
- `docs:` — documentation, registry, schemas
- `test:` — test additions or fixes
- `fix:` — bug fixes
- `infra:` — build tooling, CI, pre-commit hooks

---

## Key Constraints
- No external service calls — everything runs locally
- SHA-256 for all cryptographic operations (not SHA-1)
- Deterministic output: sorted keys in JSON, sorted hashes, sorted edges
- Append-only operation log — never delete entries
- Evidence packs are tamper-evident — changing any file invalidates the seal
- Python source files are NOT governed documents (no YYYYMMDD-VX.Y naming)
- Pre-commit hook validates governed document names, not code files
- Cowork sandbox: .git/index.lock cannot be removed — all git ops in host terminal

---

## Stack
- Python 3.13 (pyenv)
- PyYAML
- pytest
- No other runtime dependencies (by design — zero-dep governance tool)

---

## Session Efficiency
- Keep sessions to ONE feature — commit, start fresh
- This CLAUDE.md is the handoff doc; update it at session end
- **Archive rule:** when session count in "Current State" exceeds ~3, roll older sessions into `docs/session-history-YYYYMMDD-VX.Y.md` (bump its version) so this file stays slim
- Avoid reading the dashboard template (~500KB) — modify surgically
- Use subagents for parallel isolated work

---

## When to Stop and Ask
- Any change to the manifest seal algorithm requires explicit approval
- Any change to the oplog format (JSONL schema) requires approval
- Never self-initiate architectural changes — wait for instruction

## Release Process Guardrails
- **Every minor-version bump (v0.8.0+) and v1.0.0+ must include an adversarial code review phase before the release runbook runs.** CRIT and HIGH findings block the release; MED findings require explicit written acceptance in release notes to defer; LOW findings fix opportunistically. Review scope: all code changed since the last major release, focusing on shell/subprocess, path handling, TOCTOU, trust boundaries, error-swallowing, and concurrency. Self-review (Claude reviewing prior-session code) is fine — Session 52's review caught 9 real findings this way, Session 53's caught 6. See `auto-memory/feedback_major_release_adversarial_review.md` for the full protocol.
- Release runbook `-m` messages must be ASCII-only: hyphen not em-dash, no parens inside quoted strings, no `$` or backticks in nested quotes. See `auto-memory/feedback_release_runbook_ascii_only.md`.
- PyPI `/json` version-check curls after upload must `sleep 30 &&` first for CDN propagation. See `auto-memory/feedback_release_runbook_curl_lag.md`.

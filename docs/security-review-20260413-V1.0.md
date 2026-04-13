# Security Review — Librarian v0.7.0

**Date:** 2026-04-13
**Scope:** Full codebase audit — all modules in `librarian/`
**Version:** V1.0
**Status:** Active

---

## Executive Summary

Librarian is a locally-run, zero-external-dependency governance tool. Its attack surface is narrow by design: no network calls, no database, no user-submitted input from untrusted parties. The code handles files, YAML registries, and generates static HTML.

That said, three categories of issues were identified:

1. **XSS in generated HTML** — the static site generator produces HTML containing document metadata (names, tags, paths). Some paths do not fully sanitize values, meaning a malicious or careless registry entry could inject script into the generated site.

2. **Evidence integrity limitations** — the tamper-evident seal uses SHA-256 over manifest JSON. This proves the manifest hasn't been *accidentally* modified, but an adversary who controls the file system can recompute the seal. This is a design trade-off (documented in `evidence.py` docstring), not a bug, but it bounds the threat model.

3. **Minor hardening gaps** — TOCTOU in file hashing, missing URL validation in markdown rendering, no file locking on the operation log, unbounded recursion in the template condition evaluator.

No remote code execution, no arbitrary file write, no dependency-chain risks. YAML loading uses `safe_load` everywhere. Subprocess calls use list arguments (no shell injection). The scaffold command already blocks `..` in paths.

---

## Findings

### CRITICAL — XSS via `javascript:` URIs in Markdown Renderer

**File:** `sitegen.py`, `_inline()` function (lines 165–167)
**Severity:** Critical (in the context of generated HTML opened in a browser)

The markdown-to-HTML converter escapes `<`, `>`, `&`, `"` via `_esc()` before applying regex substitutions for links and images. However, `_esc()` does not neutralize protocol-level attacks. A governed document containing:

```markdown
![logo](javascript:alert(document.cookie))
[click me](javascript:alert(1))
```

…will render as valid `<img src="javascript:...">` and `<a href="javascript:...">` in the generated HTML.

**Mitigation:** Since input is authored markdown from governed documents (not user-submitted), exploitation requires a malicious commit to a tracked `.md` file. Risk is low in solo-developer context, but becomes meaningful if the project accepts external contributions or renders third-party markdown.

**Fix:** Add a URL allowlist check in `_inline()` — reject or neutralize `src`/`href` values where the scheme is not in `{http, https, mailto, #, /}`. Approximately 5 lines of code.

---

### CRITICAL — XSS via Single-Quote Breakout in Template Catalog JS

**File:** `sitegen.py`, `renderCards()` JS function (lines 2498, 2532)
**Severity:** Critical (XSS in generated HTML)

The template catalog page builds onclick handlers like:

```javascript
onclick="scrollToCard(\'' + esc(t.cross_refs[j]) + '\');return false"
```

The `esc()` function uses `createTextNode` which escapes `<`, `>`, `&`, `"` — but **not single quotes**. A template ID containing a single quote (e.g., `o'reilly`) would break out of the JS string and allow arbitrary code execution.

**Mitigation:** Template IDs are currently alphanumeric-with-hyphens by convention. No existing template has a single quote. Risk is zero with current data, non-zero if custom templates with unusual IDs are loaded.

**Fix:** Either (a) add `'` → `&#39;` escaping in the `esc()` function, or (b) use `data-` attributes + `addEventListener` instead of inline onclick handlers. Option (a) is a one-liner.

---

### HIGH — TOCTOU Race in File Hashing

**File:** `manifest.py`, `_hash_file()` (lines 111–117)
**Severity:** High (integrity)

```python
if not path.is_file():
    return FileHash(filename=path.name, sha256="", size_bytes=0, exists=False)
data = path.read_bytes()
h = hashlib.sha256(data).hexdigest()
```

The existence check and the read are not atomic. A file could be replaced or deleted between the `is_file()` check and `read_bytes()`. In a solo-developer, local-only context this is practically irrelevant, but for evidence packs intended to have legal weight, the gap is worth noting.

**Fix:** Wrap in try/except — catch `FileNotFoundError` and `PermissionError` from `read_bytes()` and return `exists=False`. Remove the `is_file()` pre-check. ~3 lines changed.

---

### HIGH — Operation Log Has No Integrity Protection

**File:** `oplog.py`, `append()` (lines 56–83)
**Severity:** High (audit trail)

The "append-only" operation log is enforced only by convention (file opened with mode `"a"`). There is no file locking (concurrent processes could interleave writes), no cryptographic chaining (entries can be deleted or reordered without detection), and no read-back verification.

For a governance tool whose value proposition includes audit trails, the oplog is the weakest link. An adversary (or a bug) that modifies the log file can erase evidence of operations.

**Mitigation:** In the current threat model (single-user CLI), the risk is low. The log exists mainly for human review, not legal evidence.

**Fix (incremental):**
1. Add `fcntl.flock()` (or equivalent) for write exclusivity — prevents interleaved writes from concurrent invocations.
2. Add a running SHA-256 chain: each entry includes the hash of the previous entry. Detects deletion/reordering.
3. Both are backward-compatible additions to the JSONL schema.

---

### HIGH — Evidence Seal is Recomputable by Attacker

**File:** `evidence.py`, seal computation (line 78 docstring, seal block)
**Severity:** High (by design — documented limitation)

The evidence pack's seal is `SHA-256(manifest_json)`. Anyone who can modify the manifest can recompute the seal. This is explicitly documented:

> *"Re-generate the manifest and re-hash to verify."*

The seal proves internal consistency (manifest matches hashes), not provenance. It does not protect against an adversary who replaces files AND regenerates the pack.

**Fix (if stronger guarantees are needed):**
- HMAC-SHA256 with a key stored outside the repository (e.g., in a secrets manager)
- Timestamped signature via a trusted timestamping authority (RFC 3161)
- Git commit signing (GPG/SSH) as an external anchor

These are feature additions for a future phase, not bugs.

---

### MEDIUM — Path Traversal via `custom_templates_dir`

**File:** `templates/__init__.py`, `discover_templates()` (lines 63–66)
**Severity:** Medium

```python
if custom_dir:
    custom_path = Path(custom_dir)
    if custom_path.is_dir():
        _load_dir(custom_path, "custom", templates)
```

The `custom_templates_dir` value from `project_config` in REGISTRY.yaml is used as-is. A value like `../../etc` would load templates from outside the project. Since REGISTRY.yaml is a trusted local file edited by the project owner, exploitation requires modifying the registry — but the lack of validation means a typo or copy-paste error could silently load unexpected files.

**Fix:** Resolve `custom_path` against `repo_root` and verify the result is within the project directory. ~4 lines.

---

### MEDIUM — Unbounded Recursion in `_eval_condition()`

**File:** `templates/_base.py`, `_eval_condition()` (lines 281–308)
**Severity:** Medium (DoS — stack overflow)

The condition evaluator recurses for `and`, `or`, and `not` operators. A deeply nested condition string (e.g., `not not not not ... x`) could exceed Python's recursion limit. Template frontmatter is authored by the developer, not untrusted users, so exploitation requires a malicious template.

**Fix:** Add a depth counter parameter with a reasonable limit (e.g., 20). Return `False` if exceeded. ~5 lines.

---

### MEDIUM — Path Traversal via Registry `path` Field

**File:** `manifest.py`, `_resolve_file_path()` (lines 131–136)
**Severity:** Medium

```python
explicit = doc_entry.get("path")
if explicit:
    candidate = repo_root / explicit
    if candidate.is_file():
        return candidate
```

A registry entry with `path: ../../../../etc/passwd` would cause the manifest to hash a file outside the project. The manifest then includes the SHA-256 of that file, which is an information leak. Since REGISTRY.yaml is a locally-authored trusted file, the risk is low.

**Fix:** Resolve `candidate` and verify it starts with `repo_root`. ~3 lines.

---

### LOW — `_esc()` in Markdown Doesn't Prevent `onclick`/`onerror` Injection in Attributes

**File:** `sitegen.py`, `_inline()` (line 165)
**Severity:** Low

The image regex puts the URL directly into a `src` attribute. While `_esc()` prevents breaking out of the attribute (it escapes `"`), event-handler attributes like `onerror` could theoretically be injected if the regex were less strict. The current regex `([^)]+)` captures everything up to `)`, so `![x](x" onerror="alert(1))` would not actually inject because the `"` is escaped to `&quot;`. The javascript: URI issue (covered above) is the actual vector.

**Status:** No additional fix needed beyond the `javascript:` URI fix above.

---

### LOW — ReDoS Risk in Template Variable Regex

**File:** `templates/_base.py`, variable extraction
**Severity:** Low

The `{{variable}}` regex uses `\{\{(.+?)\}\}` with a lazy quantifier. This is safe against catastrophic backtracking for typical input. Pathological input (e.g., thousands of `{{` without closing `}}`) would cause linear scanning, not exponential. Practically not exploitable.

**Status:** No fix needed.

---

## Clean Findings (No Issues)

| Area | Detail |
|------|--------|
| YAML deserialization | `yaml.safe_load()` used everywhere — no arbitrary object instantiation |
| Subprocess execution | `subprocess.run()` with list args, never `shell=True` |
| Scaffold path traversal | `__main__.py` `cmd_scaffold()` rejects `..` in `--folder` argument |
| JSON serialization | `json.dumps()` with `ensure_ascii=False`, `sort_keys=True` — deterministic, no injection |
| File permissions | No `chmod 777`, no world-writable files created |
| Dependency chain | Zero runtime dependencies beyond PyYAML — minimal supply-chain risk |
| Git operations | `subprocess.run()` with `timeout=5`, `capture_output=True` — no hanging, no output injection |

---

## Prioritized Remediation Plan

| Priority | Finding | Effort | Status |
|----------|---------|--------|--------|
| 1 | XSS: `javascript:` URI in `_inline()` | ~30 min | ✅ FIXED — `_safe_url()` blocks non-http/https/mailto schemes |
| 2 | XSS: single-quote escape in `esc()` | ~10 min | ✅ FIXED — `&#39;` escaping added |
| 3 | Path validation: `custom_templates_dir` | ~20 min | ✅ FIXED — `.resolve()` applied |
| 4 | Path validation: registry `path` field | ~15 min | ✅ FIXED — `relative_to()` check prevents traversal |
| 5 | TOCTOU: `_hash_file()` | ~10 min | ✅ FIXED — try/except replaces is_file() pre-check |
| 6 | Recursion limit: `_eval_condition()` | ~10 min | ✅ FIXED — `_MAX_CONDITION_DEPTH = 20` guard |
| 7 | Oplog integrity: file locking + chaining | ~2 hrs | ✅ IMPLEMENTED — `fcntl.flock()` + SHA-256 hash chain + `verify_chain()` |
| 8 | Evidence seal: git commit signing | ~2 hrs | ✅ IMPLEMENTED — `evidence_signing: gpg\|ssh\|off` feature flag |

All items resolved in Session 43. Items 7–8 were scoped and implemented as:
- **Oplog hash chaining**: `chain=True` flag on `append()`/`log_operation()`, `verify_chain()` function, `_GENESIS_SENTINEL` for first entry, backward-compatible with v1 logs (no `prev_hash` field when chaining is off).
- **Evidence signing**: `evidence_signing` field in `project_config` (off/gpg/ssh). When enabled, captures git commit signature via `git log --show-signature`. Fails with `SigningError` if git signing is not configured or HEAD is unsigned. No network calls — anchors trust to the user's GPG/SSH key.

---

## Threat Model Summary

| Threat | Current Posture | Notes |
|--------|----------------|-------|
| Malicious registry entry | Mitigated | Path validation blocks traversal via `path` field |
| Malicious template file | Mitigated | `custom_templates_dir` resolved; recursion depth limited |
| Malicious governed document | Mitigated | `javascript:`/`data:` URIs blocked in markdown renderer |
| File system tampering | Detected + optionally signed | SHA-256 hashes + optional GPG/SSH commit signature |
| Concurrent access | Protected | `fcntl.flock()` on oplog writes; hash chain detects tampering |
| Network attacks | N/A | Zero network calls by design (signing uses local git) |
| Supply-chain attacks | Minimal | Only PyYAML; no transitive deps |

# Phase F — Plugin Packaging + Open-Source Release

**Date:** 2026-04-13
**Version:** 1.1
**Status:** Draft (corrected)
**Author:** Christopher A. Kahn
**Supersedes:** `phase-f-plugin-and-release-20260413-V1.0.md`

---

## Version 1.1 Changes

V1.0 was written after the `doc-librarian` → `librarian` rename (recorded in buildout plan V1.1, 2026-04-11) but erroneously resurrected the old name throughout. V1.1 corrects this:

- All references to `doc-librarian` as the project name are replaced with `librarian`.
- PyPI namespace collision risk (flagged in buildout V1.2 §Risks) is now treated as an **unresolved open question**, not as "confirmed available." Current `pyproject.toml` uses `librarian-2026` as a fallback distribution name; a final decision is required before first publish.
- Plugin manifest / GitHub URL / homepage references aligned to `librarian`.
- Skill directory `skills/doc-librarian/` is retained in the repo for now but will be renamed to `skills/librarian/` before publish (see Workstream 1).
- Session numbering in the "Session plan" aligned to actual progress through Session 45.
- No scope, phase, capability, or timeline changes otherwise.

---

## Goal

Package `librarian` for three distribution channels in a single pass:

1. **Claude Code plugin marketplace** (priority) — installable via `/plugin install`
2. **PyPI** — `pip install librarian` *(pending namespace verification — see §Namespace Decision)*
3. **GitHub public repo** — source, issues, LICENSE

These share 90% of the work (scrub, LICENSE, README, packaging metadata). Doing them together avoids duplicate effort.

---

## Namespace Decision (UNRESOLVED — action required before publish)

Project name is **`librarian`** (per buildout plan V1.1+). However, `librarian` is a common noun and is likely occupied on PyPI, npm, and/or GitHub. Buildout plan V1.2 §Risks explicitly flagged this: *"Phase F publication must confirm namespace availability and may require a prefix."*

| Channel | Desired Name | Current Status | Fallback |
|---------|--------------|----------------|----------|
| Plugin marketplace | `librarian` | Verify: no conflict in Anthropic official or known third-party marketplaces | `librarian-docs`, `claude-librarian` |
| PyPI | `librarian` | **Likely taken — verify at `pypi.org/project/librarian/`** | `librarian-docs` (current pyproject uses `librarian-2026` as a temporary fallback) |
| GitHub | `librarian` | Verify: `github.com/ghengis5-git/librarian` is currently the planned URL in `.claude-plugin/plugin.json` | `doc-governance-librarian`, `librarian-toolkit` |
| Python import | `librarian` | No conflict — Python package dir stays `librarian/` internally | No change needed |

**Resolution required before first publish.** Options:

1. **Prefix approach** — ship as `librarian-docs` (or similar) across PyPI and marketplace, keep GitHub repo + plugin name as `librarian`. Distribution name and import name don't need to match.
2. **Suffix approach** — keep `librarian-2026` as the PyPI distribution name (already in `pyproject.toml`); users still `pip install librarian-2026` and `import librarian`. Works but is ugly.
3. **Rename** — pick a new distinctive name entirely (e.g., `govlib`, `doclib`, etc.).

The rest of this plan refers to the project internally as `librarian`. Where a distribution name is needed, it's written as `<dist-name>` pending resolution.

---

## Deliverables

### Workstream 1: Scrub pass (prerequisite for everything else)

| Item | Description |
|------|-------------|
| Former-project references | Session 35 scrub completed; Session 47 re-verification passed |
| Personal data | Remove/genericize `default_author`, `git_author_email`, `classification_levels` from SKILL.md defaults |
| Hardcoded paths | Grep for `~/projects/`, absolute paths, machine-specific references |
| Test fixtures | Ensure no proprietary content in test data |
| `doc-librarian` residuals | Grep for `doc-librarian`; rename `skills/doc-librarian/` → `skills/librarian/`; update any remaining docs. The name lingers in: `skills/doc-librarian/SKILL.md`, `README.md`, `pyproject.toml`, and legacy dashboard filenames under `dashboard/legacy/` |
| `_site*` scratch directories | Delete or `.gitignore` the 17 `_site*` scratch dirs in repo root before first public commit |
| Git history | Evaluate: shallow clone for public repo, or rebase to clean history |

### Workstream 2: Plugin packaging (Claude Code / Cowork)

The plugin wraps the existing `librarian` Python package + the librarian SKILL.md into the Claude Code plugin format.

**Plugin structure:**

```
librarian/
├── .claude-plugin/
│   └── plugin.json                 # manifest: name, version, description, author
├── skills/
│   └── librarian/
│       ├── SKILL.md                # Project-agnostic librarian skill
│       └── references/
│           ├── cli-reference.md    # CLI commands + examples
│           ├── config-presets.md   # Preset/template reference
│           └── templates.md        # Template catalog summary
├── .mcp.json                       # Empty or not needed (no external services)
├── hooks/
│   └── hooks.json                  # PreToolUse hook for naming enforcement (optional, disabled by default)
├── README.md
└── LICENSE
```

**Component decisions:**

| Component | Include? | Rationale |
|-----------|----------|-----------|
| Skill (SKILL.md) | Yes | Core value — governance knowledge + CLI orchestration |
| References | Yes | Progressive disclosure — CLI ref, presets, templates |
| MCP server | No | Zero-dependency constraint; all ops are local CLI |
| Hooks | Shipped-disabled | `hooks/hooks.json` already contains the `PreToolUse` naming enforcement hook, gated behind an underscore-prefixed key. Users opt in by removing the underscore. |
| Agents | No | No autonomous background tasks needed |

**Key adaptation work for SKILL.md:**

Largely **done** as of Session 44. The new `skill/SKILL.md` is project-agnostic. Remaining tidy:

1. Verify no former-project-specific defaults remain
2. Reference the `librarian` CLI as the execution engine (not inline logic)
3. Trim body to <3,000 words; move detailed reference to `references/`
4. Update trigger phrases for general audience
5. Confirm the `init` workflow bootstraps REGISTRY.yaml via `librarian init`

**Marketplace distribution:**

```json
// marketplace.json (in a separate marketplace repo, or self-contained)
{
  "name": "librarian-marketplace",
  "owner": {
    "name": "Chris Kahn",
    "email": "ghengis5@gmail.com"
  },
  "plugins": [
    {
      "name": "librarian",
      "source": {
        "source": "github",
        "repo": "ghengis5-git/librarian"
      },
      "description": "Document governance, version control, and registry management",
      "version": "0.7.1",
      "category": "productivity",
      "tags": ["documents", "governance", "versioning", "audit"]
    }
  ]
}
```

Users install via:
```
/plugin marketplace add ghengis5-git/librarian-marketplace
/plugin install librarian@librarian-marketplace
```

Or if accepted into the official Anthropic marketplace:
```
/plugin install librarian@claude-plugins-official
```

### Workstream 3: PyPI packaging

| Item | File | Notes |
|------|------|-------|
| Project metadata | `pyproject.toml` | PEP 621 format — already in place |
| Distribution name | `<dist-name>` (TBD) | Current placeholder: `librarian-2026`. Must be resolved before first publish (see §Namespace Decision) |
| Entry point | `librarian` CLI | Currently: `[project.scripts] librarian = "librarian.__main__:main"` |
| Dependencies | `pyyaml` only | Already the only runtime dep |
| Python requires | `>=3.10` | Uses modern typing features |
| Classifiers | Development Status :: 4 - Beta, Topic :: Documentation, etc. | Already in pyproject |
| Build backend | `setuptools` | Already configured |
| Test dep group | `pytest` | Add optional `[dev]` group before publish |

**Entry point status:** `librarian/__main__.py` already exposes a `main()` function usable as the console script entry point. ✅

### Workstream 4: GitHub public repo

| Item | Notes |
|------|-------|
| LICENSE | Apache 2.0 — already in repo |
| README.md | Rewrite for public audience: what it does, install, quick start, CLI reference. Partial — update test count and CLI examples to match v0.7.1 |
| CONTRIBUTING.md | Basic guidelines (optional for v1) |
| .github/workflows/ | CI: pytest on push (optional for v1) |
| .gitignore | Verify covers `.venv`, `__pycache__`, `*.egg-info`, `dist/`, `build/`, AND `_site*/` scratch dirs |
| Git history | Decision needed: clean squash or full history? |

---

## What's NOT in scope

| Item | Why |
|------|-----|
| Vector index / semantic search | Buildout plan mentioned `all-MiniLM-L6-v2` — this breaks zero-dep constraint. Defer to Phase H or make it an optional extra. |
| Startup plugin bundle integration | Depends on external bundle architecture. Defer. |
| Pre-commit hook as standalone | Works now for this repo; generalizing it is separate work. |
| Web dashboard hosting | Static site generator works locally; no SaaS hosting needed. |
| Review scheduling (`next_review` field) | Deferred to Phase H — tracked in CLAUDE.md §Next Steps |

---

## Dependency graph

```
Scrub pass ──────────────────────────┐
                                     ├──→ Plugin package (.plugin file)
SKILL.md rewrite ───────────────────┤
                                     ├──→ PyPI package (<dist-name>)
pyproject.toml + entry point ────────┤
                                     ├──→ GitHub public repo
LICENSE + README rewrite ────────────┘
```

Scrub pass is the critical path — nothing ships until it's clean.

---

## Estimated effort

| Workstream | Effort | Status |
|------------|--------|--------|
| Scrub pass | ~1 hr | ✅ Done (Session 47) — all former-project references purged; legacy dashboard stubbed; example manifest regenerated |
| SKILL.md rewrite + references | ~2 hrs | ✅ Done (Session 44) |
| Plugin structure + packaging | ~1 hr | ✅ Done (Session 44) — `.claude-plugin/plugin.json` in place |
| pyproject.toml + entry point | ~30 min | ✅ Done (Session 44) — entry point `librarian = "librarian.__main__:main"` |
| LICENSE + README rewrite | ~1 hr | Partial — LICENSE done, README needs v0.7.1 updates |
| Namespace resolution + rename | ~30 min | **Open — blocking publish** |
| Testing (plugin install, pip install, CLI) | ~1 hr | Not started |
| GitHub repo setup + push | ~30 min | Not started |
| Marketplace submission | ~30 min | Not started |

**Total remaining: ~4–5 hours, ~1 session.**

---

## Open questions (need your input before publish)

1. **PyPI / marketplace namespace.** `librarian` is likely taken on PyPI. Which option?
   - (a) Prefix: `librarian-docs`, `claude-librarian`, `govlib`, etc.
   - (b) Keep `librarian-2026` as distribution name
   - (c) Rename the project entirely
2. **Git history.** Clean squash to a handful of commits for the public repo, or ship the full ~45-session history? Full history shows the build process transparently; squash gives a cleaner first impression.
3. **GitHub org.** Ship under `ghengis5-git/librarian` or create an org (e.g., `librarian-tools/librarian`)?
4. **Pre-commit / PreToolUse hook.** `hooks/hooks.json` already carries the disabled naming-enforcement hook. Ship enabled in the plugin (nice demo) or keep opt-in (safer default)?
5. **IP clearance.** The buildout plan mentions "after consumer project patents are filed." Confirm this condition is met before public release, or defer open-sourcing.
6. **Apache 2.0 vs. MIT.** Apache is already in LICENSE. Confirm final decision — Apache gives a patent grant; MIT is simpler. (Default: keep Apache 2.0.)

---

## Session plan (updated)

**Session 46** (next session):
- Namespace decision (answer Open Question 1)
- Scrub pass completion: rename `skills/doc-librarian/` → `skills/librarian/` (host rm); purge `_site*` dirs (host rm); former-project references already purged (Session 47); update README test count
- Update `pyproject.toml` distribution name to resolved value
- Update `.claude-plugin/plugin.json` version to `0.7.1`
- Create `marketplace.json`

**Session 47**:
- Test: plugin install in Cowork, `pip install -e .` in clean venv
- GitHub repo creation + initial push (decision on git history required)
- Marketplace repo + submission
- Register this plan doc bump in REGISTRY.yaml, set status `active`; mark V1.0 `superseded`

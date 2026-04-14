# Phase F — Plugin Packaging + Open-Source Release

> **⚠️ SUPERSEDED** — This document is superseded by `phase-f-plugin-and-release-20260413-V1.1.md`.
> V1.0 erroneously used `doc-librarian` as the project name throughout; the project was renamed
> to `librarian` in buildout plan V1.1 (2026-04-11). Read V1.1 for the current plan.

**Date:** 2026-04-13  
**Version:** 1.0  
**Status:** Superseded  
**Author:** Christopher A. Kahn  

---

## Goal

Package `librarian` for three distribution channels in a single pass:

1. **Claude Code plugin marketplace** (priority) — installable via `/plugin install`
2. **PyPI** — `pip install doc-librarian`
3. **GitHub public repo** — source, issues, LICENSE

These share 90% of the work (scrub, LICENSE, README, packaging metadata). Doing them together avoids duplicate effort.

---

## Namespace Decision

| Channel | Name | Status |
|---------|------|--------|
| Plugin marketplace | `doc-librarian` | Available (no conflict in Anthropic official or known third-party marketplaces) |
| PyPI | `doc-librarian` | Available (confirmed — no existing package) |
| GitHub | `doc-librarian` | TBD — check `github.com/ghengis5/doc-librarian` availability |
| Python import | `librarian` | Keep as-is internally (no conflict — not a PyPI top-level import) |

Using `doc-librarian` consistently across all three channels. The Python package directory stays `librarian/` internally — the PyPI distribution name and import name don't need to match.

---

## Deliverables

### Workstream 1: Scrub pass (prerequisite for everything else)

| Item | Description |
|------|-------------|
| Former-project references | Session 35 scrub was completed — verify no regressions |
| Personal data | Remove/genericize `default_author`, `git_author_email`, `classification_levels` from SKILL.md defaults |
| Hardcoded paths | Grep for `~/projects/`, absolute paths, machine-specific references |
| Test fixtures | Ensure no proprietary content in test data |
| Git history | Evaluate: shallow clone for public repo, or rebase to clean history |

### Workstream 2: Plugin packaging (Claude Code / Cowork)

The plugin wraps the existing `librarian` Python package + the doc-librarian SKILL.md into the Claude Code plugin format.

**Plugin structure:**

```
doc-librarian/
├── .claude-plugin/
│   └── plugin.json                 # manifest: name, version, description, author
├── skills/
│   └── doc-librarian/
│       ├── SKILL.md                # Project-agnostic librarian skill
│       └── references/
│           ├── cli-reference.md    # CLI commands + examples
│           ├── config-presets.md   # Preset/template reference
│           └── templates.md        # Template catalog summary
├── .mcp.json                       # Empty or not needed (no external services)
├── hooks/
│   └── hooks.json                  # PreToolUse hook for naming enforcement (optional)
├── README.md
└── LICENSE
```

**Component decisions:**

| Component | Include? | Rationale |
|-----------|----------|-----------|
| Skill (SKILL.md) | Yes | Core value — governance knowledge + CLI orchestration |
| References | Yes | Progressive disclosure — CLI ref, presets, templates |
| MCP server | No | Zero-dependency constraint; all ops are local CLI |
| Hooks | Maybe | A `PreToolUse` hook on `Write`/`Edit` could enforce naming convention automatically. Nice-to-have, not MVP. |
| Agents | No | No autonomous background tasks needed |

**Key adaptation work for SKILL.md:**

The current `doc-librarian` SKILL.md has ~420 lines of former-project-specific defaults baked in (classification levels, naming examples, config schema). For the plugin:

1. Strip all former-project-specific defaults — make it truly project-agnostic
2. Reference the `librarian` CLI as the execution engine (not inline logic)
3. Trim body to <3,000 words; move detailed reference to `references/`
4. Update trigger phrases for general audience
5. Add `init` workflow: first-run experience that bootstraps REGISTRY.yaml via `librarian init`

**Marketplace distribution:**

```json
// marketplace.json (in a separate marketplace repo, or self-contained)
{
  "name": "doc-librarian-marketplace",
  "owner": {
    "name": "Chris Kahn",
    "email": "ghengis5@gmail.com"
  },
  "plugins": [
    {
      "name": "doc-librarian",
      "source": {
        "source": "github",
        "repo": "ghengis5/doc-librarian"
      },
      "description": "Document governance, version control, and registry management",
      "version": "0.7.0",
      "category": "productivity",
      "tags": ["documents", "governance", "versioning", "audit"]
    }
  ]
}
```

Users install via:
```
/plugin marketplace add ghengis5/doc-librarian-marketplace
/plugin install doc-librarian@doc-librarian-marketplace
```

Or if we get into the official Anthropic marketplace:
```
/plugin install doc-librarian@claude-plugins-official
```

### Workstream 3: PyPI packaging

| Item | File | Notes |
|------|------|-------|
| Project metadata | `pyproject.toml` | Replace ad-hoc setup; use modern PEP 621 format |
| Distribution name | `doc-librarian` | Maps to `librarian/` package dir |
| Entry point | `doc-librarian` CLI | `[project.scripts] doc-librarian = "librarian.__main__:main"` |
| Dependencies | `pyyaml` only | Already the only runtime dep |
| Python requires | `>=3.10` | Uses modern typing features |
| Classifiers | Development Status :: 4 - Beta, Topic :: Documentation, etc. |
| Build backend | `hatchling` or `setuptools` | Hatchling is lighter; either works |
| Test dep group | `pytest` | Optional `[dev]` group |

**Entry point note:** Currently `librarian/__main__.py` uses `argparse` and runs via `python -m librarian`. Need to extract a `main()` function (or verify one exists) for the console script entry point.

### Workstream 4: GitHub public repo

| Item | Notes |
|------|-------|
| LICENSE | Apache 2.0 (aligns with buildout plan consideration; permissive, patent grant) |
| README.md | Rewrite for public audience: what it does, install, quick start, CLI reference |
| CONTRIBUTING.md | Basic guidelines (optional for v1) |
| .github/workflows/ | CI: pytest on push (optional for v1) |
| .gitignore | Verify covers .venv, __pycache__, *.egg-info, dist/, build/ |
| Git history | Decision needed: clean squash or full history? |

---

## What's NOT in scope

| Item | Why |
|------|-----|
| Vector index / semantic search | Buildout plan mentioned `all-MiniLM-L6-v2` — this breaks zero-dep constraint. Defer to Phase H or make it an optional extra. |
| Startup plugin bundle integration | Depends on external bundle architecture. Defer. |
| Pre-commit hook as standalone | Works now for this repo; generalizing it is separate work. |
| Web dashboard hosting | Static site generator works locally; no SaaS hosting needed. |

---

## Dependency graph

```
Scrub pass ──────────────────────────┐
                                     ├──→ Plugin package (.plugin file)
SKILL.md rewrite ───────────────────┤
                                     ├──→ PyPI package (doc-librarian)
pyproject.toml + entry point ────────┤
                                     ├──→ GitHub public repo
LICENSE + README rewrite ────────────┘
```

Scrub pass is the critical path — nothing ships until it's clean.

---

## Estimated effort

| Workstream | Effort | Sessions |
|------------|--------|----------|
| Scrub pass | ~1 hr | Part of Session 44 |
| SKILL.md rewrite + references | ~2 hrs | Session 44 |
| Plugin structure + packaging | ~1 hr | Session 44 |
| pyproject.toml + entry point | ~30 min | Session 44 |
| LICENSE + README rewrite | ~1 hr | Session 44–45 |
| Testing (plugin install, pip install, CLI) | ~1 hr | Session 45 |
| GitHub repo setup + push | ~30 min | Session 45 |
| Marketplace submission | ~30 min | Session 45 |

**Total: ~7–8 hours across 2 sessions**

---

## Open questions (need your input)

1. **License**: Apache 2.0 or MIT? The buildout plan left this TBD. Apache 2.0 gives you a patent grant; MIT is simpler. Both are permissive.

2. **Git history**: Clean squash to a handful of commits for the public repo? Or ship the full 43-commit history? Full history shows the build process transparently; squash gives a cleaner first impression.

3. **GitHub org**: Ship under `ghengis5/doc-librarian` or create an org (e.g., `doc-librarian/doc-librarian`)?

4. **Pre-commit hook as plugin hook**: Worth including a `PreToolUse` hook in the plugin that auto-validates naming when Claude writes files? It's a nice demo of the hook system but adds complexity. Can defer to v0.8.

5. **IP clearance**: The buildout plan mentions "after consumer project patents are filed." Is that condition met, or does this block the public release?

---

## Session plan

**Session 44** (next session):
- Scrub pass
- Rewrite SKILL.md for plugin (project-agnostic, <3k words)
- Create references/ files
- Build plugin directory structure
- Create pyproject.toml
- Extract main() entry point

**Session 45**:
- LICENSE + README rewrite
- Test: plugin install in Cowork, pip install in clean venv
- GitHub repo creation + initial push
- Marketplace repo + submission
- Register this plan doc + bump to V1.1 with final status

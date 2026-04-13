---
name: librarian
description: "Document governance, version control, and registry management for any project. Use this skill whenever: creating, updating, or version-bumping any project document; checking what documents exist and their current versions; processing cross-reference tables from addenda to identify affected documents; enforcing a naming convention (default: descriptive-name-YYYYMMDD-VX.Y.ext); maintaining the document registry (REGISTRY.yaml); generating document status reports; or any time someone says 'update the docs', 'what version is X', 'bump the version', 'catalog this', 'what documents need updating', 'registry', 'document list', or 'version history'. Also triggers when any other skill produces a document — the librarian validates naming, updates the registry, and checks cross-references before the document is finalized."
---

# Document Librarian

A governance skill that maintains the authoritative catalog of project documentation. It enforces naming conventions, tracks versions, manages cross-references between documents, and ensures no document update orphans dependent files.

The librarian is project-agnostic. It reads project-specific rules from a `project_config` block in `REGISTRY.yaml`. When no `project_config` is present, it falls back to built-in generic defaults so it works standalone for ad hoc use.

## Getting Started — Adopting the Librarian in a New Project

To adopt the librarian in a new project:

1. **Copy this skill file** into your project's skill directory (or install the standalone `librarian` CLI — see the project README).
2. **Create `docs/REGISTRY.yaml`** with a `project_config` block tuned to your project. Start from the schema below and delete the keys you want to fall back to defaults on.
3. **Install the pre-commit hook** from `scripts/` into `.git/hooks/pre-commit`. The hook reads the same `project_config` and enforces naming convention + registry sync on every commit.
4. **Run a bootstrap scan** to seed the initial registry from files already in your `docs/` directory (see section "Initial Registry Bootstrap" below).
5. **Commit and begin governed operation.** From this point forward, every document operation should flow through the librarian.

A thin project-specific wrapper is optional. For example, a project can expose a `my-project-librarian` entry point that loads its own `project_config` from a well-known path and otherwise delegates to the generic librarian.

## Configuration Resolution

On every invocation, the librarian resolves its operating rules in this order:

1. **Read `project_config` from REGISTRY.yaml** — if the block exists and contains the needed key, use it.
2. **Fall back to built-in defaults** — if the block is missing, malformed, or a specific key is absent, use the hardcoded defaults documented in this skill file.
3. **Never fail silently** — if the registry is missing entirely, warn the operator and offer to bootstrap one.

The built-in defaults are intentionally minimal so they work for any project out of the box. Anything project-specific (author names, classification levels, tags taxonomy) should be set explicitly in `project_config`.

### project_config Schema

```yaml
project_config:
  project_name: "Example Project"           # Human-readable project name
  naming_convention: "descriptive-name-YYYYMMDD-VX.Y.ext"
  naming_rules:
    separator: "-"                           # Word separator in descriptive-name
    case: "lowercase"                        # lowercase | preserve
    forbidden_words:                         # Words banned from descriptive-name
      - "file"
      - "download"
      - "output"
      - "document"
    infrastructure_exempt:                   # Files exempt from date-version requirement
      - "SKILL.md"
      - "REGISTRY.yaml"
      - "CLAUDE.md"
      - "README.md"
      - ".gitignore"
  default_author: "Your Name"
  default_classification: "CONFIDENTIAL"
  classification_levels:
    - "CONFIDENTIAL"
    - "ATTORNEY-CLIENT PRIVILEGED"
    - "PERSONAL / INTERNAL USE ONLY"
  tags_taxonomy:
    domain:
      - architecture
      - planning
      - infrastructure
      - legal
      - operational
    phase:
      - phase-0
      - phase-1
      - phase-2
      - phase-3
    type:
      - strategic-plan
      - project-plan
      - technical-spec
      - addendum
      - analysis
      - agreement
      - report
      - diagram
    status_indicators:
      - needs-update
      - pending-review
      - blocked
  docs_path: "docs/"
  archive_path: "docs/archive/"
  diagrams_path: "docs/diagrams/"
  operator_path: "operator/phase-specs/"
  staleness_threshold_days: 90
  git_author_name: "Your Name"
  git_author_email: "your@email"
  git_commit_prefixes:
    docs: "docs:"
    registry: "registry:"
    infra: "infra:"
  os_target: "darwin"                        # darwin | linux | cross-platform
```

### Fallback Defaults

When `project_config` is absent, the librarian uses the following hardcoded values. These are intentionally generic:

| Key | Default |
|-----|---------|
| `project_name` | "Untitled Project" |
| `naming_convention` | `descriptive-name-YYYYMMDD-VX.Y.ext` |
| `separator` | `-` |
| `case` | `lowercase` |
| `forbidden_words` | file, download, output, document |
| `default_author` | (unset — must be configured) |
| `default_classification` | CONFIDENTIAL |
| `staleness_threshold_days` | 90 |
| `docs_path` | `docs/` |
| `os_target` | `darwin` |

## Why This Skill Exists

Projects with 15+ cross-referencing documents drift out of sync without a registry and enforcement layer. Versions get skipped, naming conventions break, and cross-references point to stale content. This skill prevents that.

## Core Responsibilities

### 1. Registry Maintenance

Maintain `REGISTRY.yaml` (at the path specified by `project_config` or at `docs/REGISTRY.yaml` by default) as the single source of truth for all project documentation.

Every document entry contains:

```yaml
- filename: "architectural-evolution-addendum-20260411-V1.0.docx"
  title: "Architectural Evolution Addendum"
  description: "Three-tier architecture evolution decisions and hybrid role architecture"
  format: "docx"
  version: "1.0"
  date: "2026-04-11"
  status: "active"           # draft | active | superseded | archived
  author: "Your Name"
  classification: "CONFIDENTIAL"
  locations:
    disk: true               # file exists on local filesystem
    chat: false              # file exists in Claude Chat project knowledge
    cowork: true             # same as disk (Cowork reads from disk)
  parent: null               # null if standalone, filename if addendum/supplement
  supplements:               # list of documents this one supplements
    - "technical-architecture-20260101-V1.2.docx"
  cross_references:          # sections in other docs that this doc affects
    - doc: "technical-architecture-20260101-V1.2.docx"
      sections:
        - "Section 1.1 Three-Tier Architecture"
      status: "resolved"
      resolved_date: "2026-04-11"
      resolution: "Inline pointer notes added in v1.2 bump"
  supersedes: null           # filename of document this one replaces, if any
  superseded_by: null        # filename of document that replaced this one
  tags:
    - "architecture"
```

### 2. Naming Convention Enforcement

All project documents follow the pattern specified in `project_config.naming_convention` (default: `descriptive-name-YYYYMMDD-VX.Y.ext`).

Rules:
- `descriptive-name`: uses the configured `separator` and `case`. No words from the `forbidden_words` list.
- `YYYYMMDD`: date of creation or last major revision
- `VX.Y`: version where X = major (rewrites/redesigns), Y = minor (updates/fixes within same scope)
- `ext`: file extension matching the actual format

When a document is created or renamed, validate against this pattern. If it fails, suggest the correct name before proceeding.

Examples of correct naming:
- `scientific-foundations-20260410-V1.0.docx`
- `architectural-evolution-addendum-20260411-V1.0.docx`
- `architectural-diagrams-20260411-V1.0.html`

Examples of incorrect naming:
- `output.docx` (generic name, no date, no version)
- `Architecture_V2.docx` (wrong case, no date, wrong separator)
- `docs-20260411.docx` (generic "docs", no version)

**Scope of the naming convention.** This naming convention applies to ALL files produced for the project — documents, scripts, HTML files, diagrams, config files. No exceptions. Every file that enters the repo through any tool (Chat download, Cowork creation, Claude Code generation) must comply before it is committed. Scripts follow the same pattern: `backup-20260411-V1.0.sh`, not `backup.sh`.

**Infrastructure-file exemption.** Files listed in `project_config.naming_rules.infrastructure_exempt` (default: `SKILL.md`, `REGISTRY.yaml`, `CLAUDE.md`, `README.md`, `.gitignore`) are exempt from the date-version portion of the convention because renaming them breaks tool discovery. These files must still use lowercase-hyphen descriptive names where the framework allows a choice. Rule of thumb: if a tool loads the file by a hard-coded name, the file keeps that name; everything else follows the full convention.

#### Chat Output Gate

**This is the most important enforcement point.** When operating in Claude Chat, files are created via `create_file` and delivered via `present_files`. The naming convention must be enforced at **file creation time**, not after delivery. The librarian's naming check runs as a pre-flight on every `create_file` call for project documents:

1. Before writing a file to `/mnt/user-data/outputs/` or `/home/claude/`, validate the intended filename against the naming convention.
2. If the filename fails validation, rewrite it to comply before creating the file. Do not create the non-compliant file and rename later.
3. If the file is infrastructure-exempt, skip the date-version check but still enforce lowercase-hyphen descriptive naming.
4. Log the validated filename in the session manifest.

**Why this matters:** Claude Chat's `present_files` step copies files from the working directory to the output directory. The filename set at `create_file` time is the filename the user sees in Downloads. There is no rename opportunity after `present_files` runs. If the name is wrong at creation, it's wrong in the user's Downloads folder, and telling them to rename it manually is a governance failure.

### 3. Version Bump Logic

**Minor bump (Y increment):** Content updated within existing scope. Same structure, same sections, fixes or additions that don't change the document's purpose. Example: adding two rows to a table, fixing a typo in a section, updating a cost estimate.

**Major bump (X increment):** Structural rewrite, scope expansion, or fundamental redesign. New sections added, document purpose expanded, significant reorganization. Example: adding an entirely new section to the architecture doc, merging two documents, restructuring the phase plan.

**Date update:** The YYYYMMDD portion updates whenever the version bumps. It reflects when the change was made, not the original creation date.

When bumping a version:
1. Read the current registry entry
2. Determine minor vs major based on the change scope
3. Update the filename (rename the file)
4. Update the registry entry (version, date, any new cross-references)
5. Update the version history table inside the document itself
6. Check if any other documents reference this one by filename and update those references

### 3a. File Replacement Rules

When a file is rebuilt, revised, or corrected within the same session or work period:

**Same scope, content corrected:** Bump the minor version. Example: setup script had incomplete manifest check → fixed → `V1.0` becomes `V1.1`. The old version is explicitly superseded.

**Scope expanded (new sections added):** Bump the minor version if the additions are within the original document's purpose. Bump the major version if the document's scope fundamentally changed. Example: addendum gained a new section after initial creation → that's a scope expansion → `V1.0` becomes `V1.1` or `V2.0` depending on how significant the addition is.

**Never reuse the same version for different content.** If V1.0 was delivered to the user and the content changes, the new file MUST be V1.1 or higher. Overwriting V1.0 with different content creates ambiguity — the user cannot tell which V1.0 they have.

**When presenting a replacement file to the user:**
1. State explicitly: "This replaces [filename V_X.Y] you downloaded earlier"
2. Explain what changed between versions
3. Recommend deleting the old version from Downloads to avoid confusion
4. If multiple files were produced in the session, provide a final manifest listing every file with its FINAL version number and status (current vs superseded)

### 4. Cross-Reference Processing

When an addendum or update includes a cross-reference table (a table listing which documents and sections are affected), the librarian:

1. Parses the cross-reference table
2. For each affected document, checks whether the referenced sections exist
3. Generates a checklist of required updates with specific section locations
4. Optionally executes the updates with operator approval
5. After updates complete, bumps versions on all affected documents
6. Updates the registry for all changed documents

**Pointer approach (default).** Cross-reference resolution uses inline pointer notes — a short comment inserted at the relevant section of the target document that says what changed and where to find the full detail (e.g., "See Architectural Evolution Addendum V1.0 §3 for updated three-tier architecture decisions"). This is preferred over full content integration because it preserves single-source-of-truth for the addendum content and avoids content duplication that drifts.

**Full content integration (on request).** When the operator explicitly requests it, the librarian can copy the relevant content from the addendum into the target document's section, replacing or augmenting the existing text. This creates a self-contained document but requires the operator to accept the maintenance cost of keeping two copies in sync.

This is the most important function. Without it, addenda create promises of updates that never happen, and documents drift out of sync.

### 5. Document Status Reports

On request, generate a status report showing:
- All documents with current version and last modified date
- Documents with pending cross-reference updates (addenda published but affected docs not yet updated)
- Documents approaching staleness (not updated in > `staleness_threshold_days` while active phases are progressing)
- Naming convention violations
- Missing registry entries (files in docs/ not in REGISTRY.yaml)

### 6. Archive Management

Archive management moves superseded documents out of the active docs tree into the configured `archive_path` (default: `docs/archive/`) so that the active listing shows only current documents, while preserving the full historical record. The archive is append-only: files are never deleted.

**When to archive.** Move a document to the archive when ALL of the following hold:
1. Its `status` in REGISTRY.yaml is `superseded`
2. Its successor is present on disk, registered, and has been stable for at least one full session
3. No active document has a pending cross-reference pointing at the superseded file

Do NOT archive documents that are `active`, `draft`, or `not-in-repo`, referenced by any pending cross-reference, or the current target of an in-flight version bump.

**How archived status works with the registry.** When archiving a file, update its registry entry:
- Add a `path` field pointing at the new location: `path: "docs/archive/<filename>"`
- Add a `date_archived` field with the ISO date of the archive move
- Keep `status: "superseded"` — do not change it to `"archived"` (reserved for legal/compliance retention holds)
- Leave `superseded_by` unchanged
- `locations.disk` and `locations.cowork` remain `true` — the file is still on disk, just in a subfolder

**Archive move workflow:**
1. Run a registry scan for entries with `status: superseded` and no `path` field (or a `path` outside the archive)
2. For each candidate, verify conditions 1–3 above
3. `git mv docs/<filename> docs/archive/<filename>` — use git mv, not a plain mv
4. Update the registry entry per the rules above
5. Commit per the Git Commit Workflow (section 9) — archive moves get their own commit

**Files are never deleted.** The archive is a permanent record. If a document must be legally destroyed (GDPR, litigation, regulatory retention expiry), that is a separate `status: destroyed` workflow that is OUT of scope for this skill — escalate to the project owner directly.

### 7. Environment Detection

The librarian operates in three environments with different capabilities. It detects which environment it's in and adjusts its workflow accordingly.

| Capability | Claude Chat | Cowork | Claude Code |
|---|---|---|---|
| Filesystem access | `/mnt/user-data/` only | Full (`~/projects/...`) | Full (`~/projects/...`) |
| Git operations | No | Yes | Yes |
| Multi-file cascade | Download loop | Direct in-place | Direct in-place |
| Registry read/write | Must be uploaded/downloaded | Direct | Direct |
| Naming enforcement | At `create_file` time (Chat Output Gate) | At write time | At write time |
| File delivery | `present_files` → Downloads | In-place on disk | In-place on disk |

**Detection logic:**
- If `/mnt/user-data/uploads/` exists → Claude Chat
- If `git rev-parse --git-dir` succeeds in the project directory → Cowork or Claude Code with git
- If `CLAUDE.md` is loaded as project context → Claude Code

**Chat-specific constraints:**
- Cannot rename files after `present_files`. Name must be correct at `create_file` time.
- Cannot do multi-document cascades in a single operation. Each file requires a separate download-upload cycle.
- Registry updates must be delivered as a downloadable file for the operator to install.
- **`.md` files do not deliver as downloads in Chat.** Claude Chat renders markdown inline in the conversation instead of attaching it to `present_files` output. See the "Chat `.md` → `.txt` Delivery Workaround" subsection below for the repackage convention.
- **No git access.** Chat cannot stage, commit, or inspect the repository. Any task that requires a commit, `git mv`, `git log`, or history inspection must be routed out of Chat.
- **No shell iteration.** Chat cannot run shell scripts, so any task that requires iterating on a bash hook, a lint script, or a test harness must be routed out of Chat.

**When to route a task out of Claude Chat** — stop and tell the operator to run the task in Cowork or Claude Code if **any** of the following are true. These are hard triggers, not guidelines:

1. The task modifies **3 or more** existing files on disk (cascading update).
2. The task produces or updates a **`.md` document** (Chat can't deliver it cleanly — see workaround below).
3. The task requires a **git operation** (commit, rename via `git mv`, branch inspection, history read).
4. The task requires **iterating on a shell script** (hook, lint rule, test runner, build step).
5. The task requires **running tests**.
6. The task requires **reading or writing a SQLite or other binary data store** (the Chat sandbox lacks the client libraries to iterate safely).
7. The task involves **archive moves** (`docs/` → `docs/archive/`), because the cascade of registry + cross-reference updates exceeds the cycle budget of download-upload in Chat.

When routing out, always provide the operator with: (a) the exact shell commands to run, (b) the target environment (Cowork preferred for librarian work, Claude Code for code changes), and (c) the session handoff summary the next agent will need.

**Chat `.md` → `.txt` Delivery Workaround:**

When the librarian must produce a `.md` document from within Claude Chat, Chat will render the file inline in the conversation rather than delivering it via `present_files` to Downloads. This is a platform constraint, not a file-naming bug. The workaround is:

1. Write the document content to a file with the correct stem per naming convention, but with a `.txt` extension instead of `.md`. Example: `phase-handoff-20260411-V1.0.txt`.
2. Deliver the `.txt` file via `present_files` in the normal way.
3. In the session manifest, record an explicit note for each affected file:
   > **DELIVERY NOTE:** Delivered as `.txt` due to Chat markdown rendering. **Rename to `.md` before installing at `docs/<filename>.md`.** The stem and version are correct.
4. Never edit the registry entry in Chat for a `.md` document delivered this way — registry changes must wait until the operator has installed the renamed `.md` file in Cowork/Code, where the librarian can then update `REGISTRY.yaml` in place.
5. Flag any task that would produce more than one `.md` document as a route-out trigger (rule 2 above) rather than attempting the `.txt` workaround at scale — the rename burden falls on the operator and compounds with every file.

**Why this workaround exists:** Chat's preview layer treats `.md` as a content type to display, not a file to deliver. Forcing `.txt` bypasses the preview step. The file content is identical; only the extension is adjusted for transport. This is the only governed exception to the naming convention's extension-must-match-content rule, and it is explicitly scoped to Chat delivery only. On disk, in the repo, files are always named with their semantic extension (`.md`, `.html`, `.py`, etc.).

**Cowork/Code advantages:**
- Direct filesystem access means cascading updates happen in-place.
- Git operations (commit, mv, log) are available for version tracking.
- Registry updates are written directly to disk.
- Shell scripts and tests run natively — the librarian can iterate on a hook, run the project's test suite, and commit in a single session.
- `.md` files are delivered by writing them to their final path, no extension workaround needed.

### 8. Environment Verification

Scripts default to the OS specified in `project_config.os_target` (default: `darwin` for macOS Apple Silicon). Every script must include:

- **Shebang:** `#!/bin/bash`
- **OS detection:** `OS=$(uname -s)` at the top, with the configured OS as the default/expected path
- **No GNU-specific flags** when targeting darwin: `sed -i ''`, `date -j -f`, no `--exclude` on `du`
- **No Linux assumptions** when targeting darwin: no `/proc`, no `apt`/`yum`
- **Test on the target OS first, add cross-platform compatibility second if needed.**

### 9. Git Commit Workflow

After any document operation that modifies files on disk (version bump, rename, new file, archive move, registry update), commit the changes:

1. Stage only the files that were modified in this operation
2. Write a descriptive commit message using the prefixes from `project_config.git_commit_prefixes` (default: `docs:`, `registry:`, `infra:`)
3. Include in the commit message: what changed, which documents were affected, version numbers before/after
4. Use the configured git author identity from `project_config`
5. Never batch unrelated changes into one commit
6. Never commit untracked files unless explicitly part of the current task
7. Report the commit hash in the task completion summary

## Workflow Integration

### Session Manifest Requirement

At the end of any session that produces multiple documents, generate a final manifest table listing:
- Every file produced in the session
- Its final version number
- Whether it is CURRENT (download this) or SUPERSEDED (delete this)
- Where it installs in the repo

This prevents the most common failure mode: the user downloads six files across a two-hour session, three of which were replaced by later versions, and has no way to tell which are current.

**Manifest naming-convention enforcement.** Every file in the manifest must comply with the naming convention. If Claude Chat produces a file with a non-compliant name (e.g. `SKILL.md`, `REGISTRY.yaml`), the manifest must note the compliant rename that will be applied when the file is installed in the repo. Infrastructure-exempt files note the exemption reason.

### When Another Skill Produces a Document

If the docx skill, pdf skill, pptx skill, or any other skill creates a project document:

1. Validate the filename against the naming convention
2. Create or update the registry entry
3. Check if the new document cross-references existing documents
4. Flag any documents that may need version bumps as a result
5. Confirm with the operator before executing dependent updates

### When Processing an Addendum

Addenda are the primary trigger for cascading updates. When an addendum is created:

1. Parse all cross-reference tables in the addendum
2. Build a complete update checklist across all affected documents
3. Present the checklist to the operator for review
4. Execute approved updates document by document (pointer approach by default)
5. Bump versions on all updated documents
6. Update the registry
7. Verify no circular references or orphaned cross-references remain

### When Asked "What Needs Updating?"

1. Read the registry
2. Scan for addenda whose cross-reference tables have not been fully resolved
3. Check file modification dates against registry dates (detect unregistered changes)
4. Report findings with specific action items

## Registry File Location

The registry lives at the path specified in `project_config` (default: `docs/REGISTRY.yaml`). It is version-controlled alongside all other documentation. The registry itself is infrastructure-exempt from the naming convention.

## Initial Registry Bootstrap

When first deployed against a new project, the librarian scans the docs directory recursively, identifies all existing documents, and generates the initial REGISTRY.yaml by:

1. Listing all files with recognized extensions (.docx, .md, .html, .pdf, .pptx)
2. Parsing filenames for version and date information
3. Reading document headers/titles where possible
4. Asking the operator to confirm or correct entries
5. Writing the initial registry with a `project_config` block seeded from operator answers

## Document Classification Levels

All project documents carry a classification field. The valid levels come from `project_config.classification_levels` (default: CONFIDENTIAL, ATTORNEY-CLIENT PRIVILEGED, PERSONAL / INTERNAL USE ONLY). The default for new documents comes from `project_config.default_classification` (default: CONFIDENTIAL).

The librarian preserves classification markings when updating documents and flags any document that lacks a classification.

## Error Handling

- If a file exists in the docs directory but not in the registry: flag as "unregistered" and offer to add it
- If a registry entry points to a file that doesn't exist: flag as "missing file" and offer to remove the entry or locate the file
- If two documents have the same descriptive name but different dates/versions: flag potential duplicate and ask operator to resolve
- If a cross-reference points to a section that doesn't exist in the target document: flag as "broken reference" and ask operator whether the section was renamed or removed
- If `project_config` is malformed: warn the operator, list the malformed keys, and proceed with fallback defaults for those keys

## Tags Taxonomy

Use tags from `project_config.tags_taxonomy` for categorization. A minimal default taxonomy:
- **Domain:** architecture, planning, infrastructure, legal, operational
- **Phase:** phase-0 through phase-5
- **Type:** strategic-plan, project-plan, technical-spec, addendum, analysis, agreement, report, diagram
- **Status indicators:** needs-update, pending-review, blocked

Projects should extend this taxonomy in their own `project_config.tags_taxonomy` to cover domain-specific tags.

## Integration with CLAUDE.md

When running in Claude Code, the librarian reads `CLAUDE.md` for current project state (active phase, recent commits, known issues) to contextualize document updates. For example, if CLAUDE.md shows Phase 4 is complete, the librarian can flag Phase 4 documents that haven't been updated with completion status.

## Integration with Cowork

When running in Cowork, the librarian has direct filesystem access to the project docs directory. It reads and writes files in place, uses git for version history, and can execute multi-document update cascades without the download-upload loop required in Claude Chat.

## Integration with Claude Chat

When running in Claude Chat, the librarian operates under the constraints described in section 7 (Environment Detection). Key behavioral differences:
- All naming validation happens at `create_file` time via the Chat Output Gate
- Multi-file operations are flagged with a recommendation to switch to Cowork/Code
- Registry file must be delivered as a download for the operator to install on disk
- The dashboard artifact (if available) provides a visual overview without requiring filesystem access

## Version History

| Version | Date | Notes |
|---|---|---|
| V1.0 | 2026-04-11 | Initial standalone librarian skill. Genericized examples, added "Getting Started" section and generic `project_config` schema. |

#!/bin/bash
# ============================================================
# Librarian Pre-Commit Hook — V1.0
# ============================================================
# Enforces:
#   1. Naming convention (descriptive-name-YYYYMMDD-VX.Y.ext)
#   2. Shell script macOS compatibility (no GNU-isms)
#   3. Commit hygiene (unregistered files warning)
#
# Mode: warn-and-prompt (shows violations, asks to proceed)
#
# Install (symlink, preferred — stays version-controlled):
#   ln -sf ../../scripts/librarian-pre-commit-hook-20260411-V1.0.sh \
#          .git/hooks/pre-commit
#
# ------------------------------------------------------------
# Lineage:
#   Standalone librarian pre-commit hook V1.0. Enforces the
#   canonical naming convention from commit #1. Projects that
#   adopt the librarian should edit TRACKED_DIRS and INFRA_EXEMPT
#   below to match their own layout.
#
# Features included:
#   - Forbidden-word filter
#   - /dev/tty prompt with non-interactive fallback
#   - --no-renames enumeration for accurate staging detection
#   - POSIX comment filter and sed self-reference filter
#   - session-log.md infrastructure exemption
# ============================================================

set -uo pipefail
# NOTE: intentionally no -e flag. grep returns exit 1 on no-match,
# which would kill the script during pattern checks. We handle errors
# explicitly instead.

# ── Colors ──
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Config ──
REPO_ROOT=$(git rev-parse --show-toplevel)
REGISTRY="$REPO_ROOT/docs/REGISTRY.yaml"

# Infrastructure-exempt files. Matches the default documented in
# skill/SKILL.md under project_config.naming_rules.infrastructure_exempt.
# Projects adopting the librarian should edit this list to match their
# own project_config.
INFRA_EXEMPT=(
    "SKILL.md"
    "REGISTRY.yaml"
    "CLAUDE.md"
    "README.md"
    ".gitignore"
    ".gitkeep"
    ".python-version"
    "PLAN.md"
    "ORIENT.md"
    "MEMORY.md"
    "ARCHITECTURE.md"
    "session-log.md"
    "phase-d-implementation-plan.md"
)

# Forbidden words in descriptive-name portion. Matches the default
# in skill/SKILL.md under project_config.naming_rules.forbidden_words.
FORBIDDEN_WORDS=("file" "download" "output" "document")

# Directories to skip naming checks on (not document directories).
# The librarian's naming convention applies to docs and skill files,
# not to source code or virtualenvs.
SKIP_DIRS=("src/" "lib/" "node_modules/" ".git/" "__pycache__/" ".venv/" "venv/" "data/" "build/" "dist/" "librarian/" "tests/" "scripts/" "site/" "site_output/" "examples/" "schema/" "dashboard/")

# Document extensions that the naming convention applies to.
# NOTE: .py is excluded — Python source files are NOT governed documents.
DOC_EXTENSIONS=("docx" "md" "html" "pdf" "pptx" "txt" "sh" "yaml" "yml" "jsx" "css" "js" "json")

# Tracked directories for the registry-sync check. The hook only
# flags unregistered files in these directories. Projects adopting
# the librarian should edit this list to match their own layout.
TRACKED_DIRS=("docs/" "skill/")

warnings=0
errors=0
messages=""

warn() {
    messages+="${YELLOW}  ⚠ $1${RESET}\n"
    warnings=$((warnings + 1))
}

err() {
    messages+="${RED}  ✗ $1${RESET}\n"
    errors=$((errors + 1))
}

info() {
    messages+="${CYAN}  ℹ $1${RESET}\n"
}

ok() {
    messages+="${GREEN}  ✓ $1${RESET}\n"
}

section() {
    messages+="\n${BOLD}── $1 ──${RESET}\n"
}

# ============================================================
# 1. NAMING CONVENTION CHECK
# ============================================================

section "Naming Convention"

# Get staged files (added or modified, not deleted).
# --no-renames forces git to show add+delete pairs rather than collapsing
# them into a single rename entry. Without this, staging a new file
# that's similar to an about-to-be-deleted one causes git to report
# only the rename, which is not in --diff-filter=ACM, and the new file
# is silently skipped by the linter.
staged_files=$(git diff --cached --no-renames --name-only --diff-filter=ACM 2>/dev/null || true)

if [ -z "$staged_files" ]; then
    info "No files staged"
else
    naming_checked=0
    naming_passed=0
    naming_warned=0

    while IFS= read -r filepath; do
        filename=$(basename "$filepath")
        ext="${filename##*.}"
        name_no_ext="${filename%.*}"

        # Skip files in non-document directories
        skip=false
        for skip_dir in "${SKIP_DIRS[@]}"; do
            if [[ "$filepath" == "$skip_dir"* ]]; then
                skip=true
                break
            fi
        done
        $skip && continue

        # Skip files with non-document extensions
        ext_match=false
        for doc_ext in "${DOC_EXTENSIONS[@]}"; do
            if [[ "$ext" == "$doc_ext" ]]; then
                ext_match=true
                break
            fi
        done
        $ext_match || continue

        naming_checked=$((naming_checked + 1))

        # Check infrastructure exemption
        is_exempt=false
        for exempt in "${INFRA_EXEMPT[@]}"; do
            if [[ "$filename" == "$exempt" ]]; then
                is_exempt=true
                break
            fi
        done

        if $is_exempt; then
            # Exempt files: only check lowercase-hyphen where possible.
            # Conventional uppercase files (CLAUDE.md, README.md, PLAN.md,
            # ORIENT.md, MEMORY.md, ARCHITECTURE.md) are allowed as-is.
            if [[ "$filename" =~ [A-Z] ]] \
                && [[ "$filename" != "CLAUDE.md" ]] \
                && [[ "$filename" != "README.md" ]] \
                && [[ "$filename" != "PLAN.md" ]] \
                && [[ "$filename" != "ORIENT.md" ]] \
                && [[ "$filename" != "MEMORY.md" ]] \
                && [[ "$filename" != "ARCHITECTURE.md" ]]; then
                info "$filename — infrastructure-exempt (uppercase allowed for this file)"
            fi
            naming_passed=$((naming_passed + 1))
            continue
        fi

        # ── Full naming convention validation ──
        file_warnings=0

        # Extract descriptive name (everything before the date or version).
        if [[ "$name_no_ext" =~ ^(.+)-[0-9]{8}-V[0-9]+\.[0-9]+$ ]]; then
            descriptive="${BASH_REMATCH[1]}"
            has_date=true
            has_version=true
        elif [[ "$name_no_ext" =~ ^(.+)-[0-9]{8}$ ]]; then
            descriptive="${BASH_REMATCH[1]}"
            has_date=true
            has_version=false
        elif [[ "$name_no_ext" =~ ^(.+)-V[0-9]+\.[0-9]+$ ]]; then
            descriptive="${BASH_REMATCH[1]}"
            has_date=false
            has_version=true
        else
            descriptive="$name_no_ext"
            has_date=false
            has_version=false
        fi

        # Check: has date
        if ! $has_date; then
            warn "$filename — missing YYYYMMDD date"
            file_warnings=$((file_warnings + 1))
        fi

        # Check: has version
        if ! $has_version; then
            warn "$filename — missing VX.Y version suffix"
            file_warnings=$((file_warnings + 1))
        fi

        # Check: lowercase
        if [[ "$descriptive" =~ [A-Z] ]]; then
            warn "$filename — descriptive name contains uppercase: '$descriptive'"
            file_warnings=$((file_warnings + 1))
        fi

        # Check: hyphen-separated (no underscores)
        if [[ "$descriptive" =~ _ ]]; then
            warn "$filename — uses underscores instead of hyphens: '$descriptive'"
            file_warnings=$((file_warnings + 1))
        fi

        # Check: no forbidden words
        descriptive_lower=$(echo "$descriptive" | tr '[:upper:]' '[:lower:]')
        for word in "${FORBIDDEN_WORDS[@]}"; do
            if [[ "$descriptive_lower" =~ (^|-)${word}(-|$) ]]; then
                warn "$filename — contains forbidden word: '$word'"
                file_warnings=$((file_warnings + 1))
            fi
        done

        # Check: no spaces
        if [[ "$filename" =~ \  ]]; then
            warn "$filename — contains spaces"
            file_warnings=$((file_warnings + 1))
        fi

        if [ "$file_warnings" -eq 0 ]; then
            naming_passed=$((naming_passed + 1))
        else
            naming_warned=$((naming_warned + 1))
        fi

    done <<< "$staged_files"

    if [ "$naming_checked" -eq 0 ]; then
        info "No document files in this commit"
    else
        ok "$naming_passed/$naming_checked files pass naming convention"
        if [ "$naming_warned" -gt 0 ]; then
            warn "$naming_warned file(s) have naming issues"
        fi
    fi
fi

# ============================================================
# 2. SHELL SCRIPT macOS COMPATIBILITY CHECK
# ============================================================

section "Shell Compatibility (macOS/Darwin)"

shell_files=$(echo "$staged_files" | grep '\.sh$' || true)

if [ -z "$shell_files" ]; then
    info "No shell scripts in this commit"
else
    shell_checked=0
    shell_clean=0

    while IFS= read -r shfile; do
        [ -z "$shfile" ] && continue
        shell_checked=$((shell_checked + 1))
        file_issues=0
        full_path="$REPO_ROOT/$shfile"

        # Skip if file doesn't exist (deleted)
        [ -f "$full_path" ] || continue

        # Helper: grep for a pattern, excluding comments, string literals in
        # warn/echo/info/err lines, and the hook's own lint_check invocations
        # (which would otherwise self-match because the pattern strings
        # themselves appear on those lines).
        # Usage: lint_check "pattern" "message"
        lint_check() {
            local pattern="$1"
            local msg="$2"
            local matches
            matches=$(grep -n "$pattern" "$full_path" 2>/dev/null \
                | grep -v '^[0-9]*:[[:space:]]*#' \
                | grep -v 'warn ' \
                | grep -v 'echo ' \
                | grep -v 'info ' \
                | grep -v 'err ' \
                | grep -v 'lint_check ' \
                || true)
            if [ -n "$matches" ]; then
                local line
                line=$(echo "$matches" | head -1 | cut -d: -f1)
                warn "$shfile:$line — $msg"
                file_issues=$((file_issues + 1))
            fi
        }

        # Check: sed -i without '' (GNU sed vs BSD sed).
        # Filter excludes: properly-quoted forms, comments, warn/echo output
        # lines, and the sed_matches= definition line itself (which would
        # otherwise self-match because 'sed -i[' appears in the grep pattern).
        sed_matches=$(grep -n 'sed -i[^[:space:]]' "$full_path" 2>/dev/null \
            | grep -v "sed -i ''" \
            | grep -v 'sed -i ""' \
            | grep -v '^[0-9]*:[[:space:]]*#' \
            | grep -v 'warn ' \
            | grep -v 'echo ' \
            | grep -v 'sed_matches=' \
            || true)
        if [ -n "$sed_matches" ]; then
            line=$(echo "$sed_matches" | head -1 | cut -d: -f1)
            warn "$shfile:$line — sed -i without '' (breaks on macOS, use: sed -i '' 's/.../')"
            file_issues=$((file_issues + 1))
        fi

        lint_check 'date -d[[:space:]]' "date -d is GNU-only (use: date -j -f on macOS)"
        lint_check 'du --exclude' "du --exclude not available on macOS"
        lint_check 'readlink -f' "readlink -f is GNU-only (use: realpath or python -c on macOS)"
        lint_check '/proc/' "/proc/ does not exist on macOS"
        lint_check 'apt-get\|apt install\|yum \|dnf ' "Linux package manager (use: brew on macOS)"
        lint_check 'stat --format\|stat -c' "stat --format/-c is GNU-only (use: stat -f on macOS)"
        lint_check 'tar.*--exclude-vcs\|tar.*--transform' "GNU tar flag (BSD tar on macOS uses different syntax)"

        # Check: missing shebang
        first_line=$(head -1 "$full_path" 2>/dev/null)
        if [[ ! "$first_line" =~ ^#! ]]; then
            warn "$shfile — missing shebang line"
            file_issues=$((file_issues + 1))
        fi

        if [ "$file_issues" -eq 0 ]; then
            shell_clean=$((shell_clean + 1))
        fi

    done <<< "$shell_files"

    ok "$shell_clean/$shell_checked shell scripts pass macOS compatibility"
fi

# ============================================================
# 3. UNREGISTERED FILE CHECK
# ============================================================

section "Registry Sync"

if [ -f "$REGISTRY" ]; then
    unregistered=0

    while IFS= read -r filepath; do
        [ -z "$filepath" ] && continue
        filename=$(basename "$filepath")

        # Only check files in tracked directories
        in_tracked=false
        for tracked in "${TRACKED_DIRS[@]}"; do
            if [[ "$filepath" == "$tracked"* ]]; then
                in_tracked=true
                break
            fi
        done
        $in_tracked || continue

        # Check document extensions only
        ext="${filename##*.}"
        is_doc=false
        for doc_ext in "docx" "md" "html" "pdf" "pptx" "jsx"; do
            if [[ "$ext" == "$doc_ext" ]]; then
                is_doc=true
                break
            fi
        done
        $is_doc || continue

        # Skip infrastructure-exempt
        is_exempt=false
        for exempt in "${INFRA_EXEMPT[@]}"; do
            if [[ "$filename" == "$exempt" ]]; then
                is_exempt=true
                break
            fi
        done
        $is_exempt && continue

        # Check registry — match against both 'filename:' key and 'path:' key
        # REGISTRY.yaml stores filenames as unquoted YAML values:
        #   filename: my-doc-20260412-V1.0.md
        #   path: docs/my-doc-20260412-V1.0.md
        if ! grep -qE "(filename|path):.*$filename" "$REGISTRY" 2>/dev/null; then
            warn "$filepath — not found in REGISTRY.yaml"
            unregistered=$((unregistered + 1))
        fi

    done <<< "$staged_files"

    if [ "$unregistered" -eq 0 ]; then
        ok "All staged document files are registered"
    else
        warn "$unregistered file(s) not in REGISTRY.yaml — register before or after commit"
    fi
else
    warn "REGISTRY.yaml not found at $REGISTRY — skipping registry sync check"
fi

# ============================================================
# SUMMARY AND PROMPT
# ============================================================

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}  Librarian Pre-Commit Check${RESET}"
echo -e "${BOLD}═══════════════════════════════════════════════════${RESET}"
echo -e "$messages"
echo -e "${BOLD}───────────────────────────────────────────────────${RESET}"

if [ "$warnings" -eq 0 ] && [ "$errors" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}  All checks passed.${RESET}"
    echo -e "${BOLD}═══════════════════════════════════════════════════${RESET}"
    echo ""
    exit 0
fi

if [ "$errors" -gt 0 ]; then
    echo -e "${RED}${BOLD}  $errors error(s), $warnings warning(s)${RESET}"
else
    echo -e "${YELLOW}${BOLD}  $warnings warning(s), 0 errors${RESET}"
fi
echo -e "${BOLD}═══════════════════════════════════════════════════${RESET}"
echo ""

# Warn-and-prompt: ask to proceed.
#
# Test /dev/tty directly instead of [ -t 0 ]. Git invokes hooks with
# stdin attached to whatever git inherited; /dev/tty is the controlling
# terminal regardless of stdin state. If /dev/tty is unavailable (CI,
# cron, piped git commits), fall back to the hard-block path.
if { : > /dev/tty; } 2>/dev/null; then
    echo -en "${YELLOW}Proceed with commit? (y/N): ${RESET}" > /dev/tty
    read -r response < /dev/tty
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Proceeding...${RESET}" > /dev/tty
        exit 0
    else
        echo -e "${RED}Commit aborted.${RESET}" > /dev/tty
        exit 1
    fi
else
    # No controlling terminal — block on errors, pass on warnings-only
    if [ "$errors" -gt 0 ]; then
        echo -e "${RED}Non-interactive mode — commit blocked due to errors.${RESET}"
        echo -e "Run: ${CYAN}git commit --no-verify${RESET} to bypass."
        exit 1
    else
        echo -e "${YELLOW}Non-interactive mode — proceeding with warnings.${RESET}"
        exit 0
    fi
fi

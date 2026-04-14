#!/bin/bash
# ============================================================
# Librarian Oplog Lock — V1.0 (Phase 7.5)
# ============================================================
# Apply, remove, or query the OS-level append-only flag on the
# librarian operation log. This promotes the detect-only hash
# chain to a prevention-mode audit trail: once the flag is set,
# the kernel denies any open that doesn't use O_APPEND, so
# modification or truncation of past entries returns EPERM.
#
# Cross-platform:
#   * macOS:   chflags uappend|nouappend  (no sudo; owner only)
#   * Linux:   chattr +a|-a              (requires sudo / CAP_LINUX_IMMUTABLE)
#
# Usage:
#   ./librarian-oplog-lock-20260414-V1.0.sh status   [log_path]
#   ./librarian-oplog-lock-20260414-V1.0.sh lock     [log_path]
#   ./librarian-oplog-lock-20260414-V1.0.sh unlock   [log_path]
#
# Default log_path: ./operator/librarian-audit.jsonl (matches
# librarian.oplog._default_log_path).
# ============================================================

set -uo pipefail

RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

usage() {
    cat <<USAGE
Usage: $0 {status|lock|unlock} [log_path]

  status    Print whether the log file has the append-only flag set.
  lock      Apply the append-only flag (OS-specific).
  unlock    Remove the append-only flag (OS-specific).

Default log_path: operator/librarian-audit.jsonl
USAGE
    exit 2
}

[ $# -ge 1 ] || usage
action="$1"
log_path="${2:-operator/librarian-audit.jsonl}"

# Detect OS. Phase 8.0: dropped the ``2>/dev/null || echo unknown``
# fallback — ``uname -s`` is in POSIX and is guaranteed to exist on
# every system this script actually runs on. If it ever fails, we want
# the failure to surface rather than be silently relabeled "unknown".
uname_out="$(uname -s)"
case "$uname_out" in
    Darwin)  os="macos" ;;
    Linux)   os="linux" ;;
    *)       os="unsupported" ;;
esac

if [ "$os" = "unsupported" ]; then
    echo -e "${RED}Error:${RESET} OS '$uname_out' is not supported for append-only locking."
    echo "This script works on macOS (chflags) and Linux (chattr) only."
    exit 1
fi

# Ensure the log file exists for lock/unlock — empty is fine.
if [ "$action" != "status" ] && [ ! -f "$log_path" ]; then
    mkdir -p "$(dirname "$log_path")"
    : > "$log_path"
    echo -e "${CYAN}Created empty log file:${RESET} $log_path"
fi

is_locked() {
    local f="$1"
    [ -f "$f" ] || { echo "missing"; return; }
    if [ "$os" = "macos" ]; then
        # stat -f '%f' returns flags as a decimal integer on BSD;
        # UF_APPEND is 0x04. Phase 8.0: distinguish "stat failed" from
        # "stat reported zero". The prior ``|| echo 0`` swallowed
        # permission-denied / syscall errors and reported "unlocked"
        # (a false all-clear). Now stat failure surfaces as "unknown".
        local flags stat_rc
        flags=$(stat -f '%f' "$f" 2>/dev/null)
        stat_rc=$?
        if [ $stat_rc -ne 0 ] || [ -z "$flags" ]; then
            echo "unknown"
            return
        fi
        if (( flags & 4 )); then echo "locked"; else echo "unlocked"; fi
    else
        # Linux — parse lsattr, but treat non-zero exit (e.g., unsupported
        # filesystem like overlayfs) as "unknown" instead of silently reporting
        # "unlocked". Otherwise we'd give a false all-clear on containers and
        # some network mounts.
        if ! command -v lsattr >/dev/null 2>&1; then
            echo "unknown"
            return
        fi
        local out rc
        out=$(lsattr -d "$f" 2>/dev/null)
        rc=$?
        if [ $rc -ne 0 ] || [ -z "$out" ]; then
            echo "unknown"
            return
        fi
        local col
        col=$(echo "$out" | awk '{print $1}')
        if [[ "$col" == *a* ]]; then echo "locked"; else echo "unlocked"; fi
    fi
}

case "$action" in
    status)
        state=$(is_locked "$log_path")
        case "$state" in
            locked)
                echo -e "${GREEN}${BOLD}locked${RESET}    $log_path"
                echo "  The oplog is kernel-enforced append-only. Attempts to"
                echo "  truncate or rewrite past entries will return EPERM."
                ;;
            unlocked)
                echo -e "${YELLOW}${BOLD}unlocked${RESET}  $log_path"
                echo "  The oplog has NO OS-level tampering protection."
                echo "  To enable: $0 lock $log_path"
                ;;
            missing)
                echo -e "${YELLOW}${BOLD}missing${RESET}   $log_path"
                echo "  Log file does not exist yet. Run a librarian operation"
                echo "  (register, bump, scaffold, audit) to create it, then"
                echo "  re-run this script."
                ;;
            unknown)
                echo -e "${YELLOW}${BOLD}unknown${RESET}   $log_path"
                echo "  Could not detect flag state. On Linux, this usually"
                echo "  means lsattr is not installed or the filesystem does"
                echo "  not support file attributes."
                ;;
        esac
        ;;

    lock)
        prior=$(is_locked "$log_path")
        if [ "$prior" = "locked" ]; then
            echo -e "${GREEN}Already locked:${RESET} $log_path"
            exit 0
        fi
        if [ "$os" = "macos" ]; then
            chflags uappend "$log_path"
            rc=$?
        else
            echo -e "${CYAN}Linux requires sudo for chattr +a:${RESET}"
            sudo chattr +a "$log_path"
            rc=$?
        fi
        if [ $rc -ne 0 ]; then
            echo -e "${RED}Failed to apply append-only flag.${RESET}"
            exit $rc
        fi
        after=$(is_locked "$log_path")
        if [ "$after" = "locked" ]; then
            echo -e "${GREEN}${BOLD}Locked:${RESET} $log_path"
            echo "  The oplog is now kernel-enforced append-only."
            echo "  To remove: $0 unlock $log_path"
        else
            echo -e "${RED}Lock command ran but flag did not take effect.${RESET}"
            exit 1
        fi
        ;;

    unlock)
        prior=$(is_locked "$log_path")
        if [ "$prior" = "unlocked" ]; then
            echo -e "${YELLOW}Already unlocked:${RESET} $log_path"
            exit 0
        fi
        if [ "$os" = "macos" ]; then
            chflags nouappend "$log_path"
            rc=$?
        else
            echo -e "${CYAN}Linux requires sudo for chattr -a:${RESET}"
            sudo chattr -a "$log_path"
            rc=$?
        fi
        if [ $rc -ne 0 ]; then
            echo -e "${RED}Failed to remove append-only flag.${RESET}"
            exit $rc
        fi
        echo -e "${GREEN}Unlocked:${RESET} $log_path"
        echo "  The append-only flag has been removed. Normal writes"
        echo "  (including log rotation or cleanup) are now permitted."
        ;;

    *)
        usage
        ;;
esac

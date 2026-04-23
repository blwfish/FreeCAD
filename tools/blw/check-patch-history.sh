#!/usr/bin/env bash
# check-patch-history.sh — audit blw-fixes-v5 patches against upstream history
#
# For each patch on blw-fixes-v5 that is not present on the upstream base, search
# upstream for closed PRs touching the same files. Flag patches whose touched
# files appear in upstream commits since our base — those may be conflicting
# with upstream-rejected work (the patch 2 / PR #25913 / PR #26596 pattern).
#
# Usage: bash tools/blw/check-patch-history.sh [base-ref]
#   base-ref defaults to weekly-2026.04.15
#
# Requires: gh CLI authenticated against FreeCAD/FreeCAD

set -euo pipefail

REPO="FreeCAD/FreeCAD"
BASE="${1:-weekly-2026.04.15}"

if ! command -v gh >/dev/null 2>&1; then
    echo "error: gh CLI required" >&2
    exit 1
fi

if ! git rev-parse --verify "$BASE" >/dev/null 2>&1; then
    echo "error: base ref '$BASE' not found" >&2
    exit 1
fi

echo "Auditing patches on $(git symbolic-ref --short HEAD) since $BASE"
echo "Repo: $REPO"
echo

# Iterate patches in apply order (oldest first). Skip merges and pre-commit.ci.
PATCHES=$(git log --reverse --no-merges --format='%H %s' "$BASE..HEAD" \
            | grep -vE '^\S+ \[pre-commit\.ci\]' \
            || true)

if [[ -z "$PATCHES" ]]; then
    echo "No patches between $BASE and HEAD."
    exit 0
fi

echo "$PATCHES" | while IFS= read -r line; do
    SHA="${line%% *}"
    SUBJECT="${line#* }"
    SHORT="${SHA:0:10}"

    FILES=$(git show --name-only --format= "$SHA" | grep -v '^$' || true)
    [[ -z "$FILES" ]] && continue

    # Look for upstream commits since BASE that touched the same files.
    UPSTREAM_TOUCHED=""
    while IFS= read -r f; do
        UPSTREAM=$(git log --format='%h %s' "$BASE..origin/main" -- "$f" 2>/dev/null | head -3 || true)
        if [[ -n "$UPSTREAM" ]]; then
            UPSTREAM_TOUCHED+="  $f:"$'\n'"$UPSTREAM"$'\n'
        fi
    done <<< "$FILES"

    if [[ -n "$UPSTREAM_TOUCHED" ]]; then
        echo "─── $SHORT  $SUBJECT"
        echo "Upstream commits since $BASE touching same files:"
        echo "$UPSTREAM_TOUCHED"
    fi
done

echo
echo "Done. Manually review any flagged patches against upstream PRs:"
echo "  gh pr list --repo $REPO --state closed --search '<symbol or filename>'"

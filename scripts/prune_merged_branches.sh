#!/usr/bin/env bash
#
# prune_merged_branches.sh
#
# Intended for interactive use only. Do not run non-interactively or in automation.
#
# This script helps you interactively prune (delete) remote branches that have been merged into a selected 'develop*' branch.
# It lists all remote branches starting with 'develop', lets you choose a target branch, and then finds branches merged into it
# that are older than a minimum age (default: 2 weeks). You are shown a list of candidates and must confirm deletion of the list
# of branches interactively.
#
# Usage: ./prune_merged_branches.sh
#
# You will be prompted to select a target branch and confirm deletion.

# === Global Variables ===
# MIN_AGE_IN_WEEKS: Minimum age (in weeks) a merged branch must be before being eligible for deletion.
#                   Default: 2 (settable by editing this script).
# REMOTE:           The name of the remote to operate on (e.g., 'origin').
#                   Default: origin.
MIN_AGE_IN_WEEKS=2
REMOTE=origin

# Select target branch dynamically from remote branches starting with 'develop*'
echo "Fetching remote branches..."
git fetch --quiet --prune

DEVELOP_BRANCHES=()
while IFS= read -r branch_name; do
    [ -n "$branch_name" ] && DEVELOP_BRANCHES+=("$branch_name")
done < <(git branch -r --format='%(refname:short)' | sed 's/^[[:space:]]*//' | grep -E "^${REMOTE}/develop" | sed "s|^${REMOTE}/||" | sort -u)

if [ ${#DEVELOP_BRANCHES[@]} -eq 0 ]; then
    echo "No remote branches starting with 'develop' found."
    exit 1
fi

echo "Available 'develop*' branches:"
select TARGET_BRANCH in "${DEVELOP_BRANCHES[@]}"; do
    if [ -n "$TARGET_BRANCH" ]; then
        echo "Selected target branch: $TARGET_BRANCH"
        break
    else
        echo "Invalid selection. Please choose a number from the list."
    fi
done

# Get today's date in seconds
NOW=$(date +%s)

# Collect candidates to delete after confirmation
candidates=()

# List candidate merged branches
for branch in $(git branch -r --merged $REMOTE/$TARGET_BRANCH | grep -vE "$TARGET_BRANCH" | sed 's/${REMOTE}\///'); do
    # Get the latest commit date for the branch in seconds since epoch
    LAST_COMMIT=$(git log -1 --format="%ct" $REMOTE/$branch)
    AGE=$(( (NOW - LAST_COMMIT) / (60*60*24*7) ))  # Age in weeks

    if [ $AGE -ge $MIN_AGE_IN_WEEKS ]; then
        candidates+=("$branch")
    fi   
done

if [ ${#candidates[@]} -eq 0 ]; then
    echo "No branches eligible for deletion."
    exit 0
fi

echo ""
echo "The following branches are eligible for deletion (>= $MIN_AGE_IN_WEEKS weeks merged into $REMOTE/$TARGET_BRANCH):"
for branch in "${candidates[@]}"; do
    echo " - $branch"
done

# Require a simple math confirmation before deleting the previously listed branches
n1=$(( (RANDOM % 8) + 3 ))
n2=$(( (RANDOM % 8) + 2 ))
read -r -p "☠️  To confirm deletion of ${#candidates[@]} branches, what is $n1 + $n2?  ☠️ :" answer

if [[ "$answer" =~ ^[0-9]+$ ]] && [ "$answer" -eq $((n1 + n2)) ]; then
    echo "Answer correct. Deleting branches..."
    for branch in "${candidates[@]}"; do
        git push "$REMOTE" --delete "${branch#origin/}"
    done
    echo "Deletion completed."
else
    echo "Incorrect answer. Aborting without deleting any branches."
    exit 1
fi

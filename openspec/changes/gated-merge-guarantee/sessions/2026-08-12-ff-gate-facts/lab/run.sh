#!/bin/zsh
# Exercise `wt merge` on a given branch shape and report which hooks fired.
WT=/nix/store/i5zr65bbyaxdvzgq750ydp7c3g6pwl2d-worktrunk-0.57.0/bin/wt
CFG=${WTLAB_CFG:-/tmp/wtlab/userconf/config.toml}
PROJ=/tmp/wtlab/proj
name=$1; shift            # scenario name
setup=$1; shift           # shell snippet run inside the branch worktree
mergeargs=("$@")

cd $PROJ
git checkout -q main 2>/dev/null
git reset -q --hard $(cat /tmp/wtlab/BASE)
git worktree remove --force /tmp/wtlab/proj.$name 2>/dev/null
git branch -D $name 2>/dev/null >/dev/null
git checkout -q main
git worktree add -q -b $name /tmp/wtlab/proj.$name main
cd /tmp/wtlab/proj.$name
git config user.email lab@example.com; git config user.name Lab
eval "$setup"

export WTLAB_LOG=/tmp/wtlab/log.$name
: > $WTLAB_LOG
print -r -- "############ SCENARIO: $name   (wt merge ${mergeargs})"
print -r -- "--- before: main=$(git -C $PROJ rev-parse --short main)  $name=$(git rev-parse --short HEAD)  status=$(git status --porcelain | wc -l | tr -d ' ') files"
print -r -- "--- merge output:"
$WT --config $CFG -C /tmp/wtlab/proj.$name merge "${mergeargs[@]}" main >/tmp/wtlab/out.$name 2>&1; rc=$?
sed "s/^/    /" /tmp/wtlab/out.$name
print -r -- "--- wt exit code = $rc"
print -r -- "--- hooks that fired:"
if [[ -s $WTLAB_LOG ]]; then sed 's/^/    /' $WTLAB_LOG; else print -r -- "    (NONE)"; fi
print -r -- "--- after: main=$(git -C $PROJ rev-parse --short main) payload=$(git -C $PROJ show main:payload.txt 2>/dev/null)"
print -r -- "--- main history:"
git -C $PROJ log --oneline --graph -4 main | sed 's/^/    /'
print -r --

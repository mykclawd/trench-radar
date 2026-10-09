#!/usr/bin/env bash
# Mechanical quality gate for a Trench Radar report.
# Usage: scripts/audit.sh <reports_dir> <YYYY-MM-DD> [run_start_marker]
#   reports_dir: the directory served as /trenches (holds <date>/index.html and index.html)
#   run_start_marker: file touched at run start (default /tmp/trench-run-start); skipped if missing
# Image srcs of the form /trenches/... are resolved against reports_dir.
# Exit 0 = pass, 1 = at least one failure (every failure is printed).
set -uo pipefail

reports=${1:?usage: audit.sh <reports_dir> <YYYY-MM-DD> [run_start_marker]}
date=${2:?usage: audit.sh <reports_dir> <YYYY-MM-DD> [run_start_marker]}
marker=${3:-/tmp/trench-run-start}
files=("$reports/$date/index.html" "$reports/index.html")
fail=0
bad() { echo "FAIL: $*"; fail=1; }

# Visible text only: strip attribute values that legitimately carry dates (URLs, meta content).
visible() { sed -E 's/(href|src|content)="[^"]*"//g' "$1"; }

for f in "${files[@]}"; do
  echo "== $f"
  [[ -f $f ]] || { bad "missing"; continue; }

  size=$(wc -c <"$f")
  (( size > 5000 )) || bad "only $size bytes"
  grep -q "$date" "$f" || bad "does not contain $date"
  if [[ -f $marker ]]; then
    [[ $f -nt $marker ]] || bad "not newer than $marker (stale file, regenerate)"
  fi

  # Stale dates: any month-year or ISO date in visible text that is not today.
  today_long=$(date -d "$date" '+%B %-d, %Y')
  while IFS= read -r hit; do
    [[ -z $hit ]] && continue
    [[ $hit == "$date" || $today_long == "$hit"* ]] && continue
    bad "date in visible text: '$hit'"
  done < <(visible "$f" | grep -oiP '(january|february|march|april|may|june|july|august|september|october|november|december)[^.<]{0,24}[0-9]{4}|[0-9]{4}-[0-9]{2}-[0-9]{2}')

  n=$(grep -cP '—|–' "$f"); (( n == 0 )) || bad "$n lines with em/en dashes"
  n=$(grep -ciP 'force.?includ|forced in|why it.?s here' "$f"); (( n == 0 )) || bad "$n lines with banned selection jargon"

  heroes=$(grep -o 'class="hero"' "$f" | wc -l); (( heroes <= 1 )) || bad "$heroes hero figures"
  stories=$(grep -o 'class="story-img"' "$f" | wc -l); (( stories <= 3 )) || bad "$stories story images (max 3)"

  while IFS= read -r src; do
    case $src in
      http://*|https://*) bad "hotlinked image $src" ;;
      /trenches/*) [[ -s $reports/${src#/trenches/} ]] || bad "image file missing for $src" ;;
      *) bad "unexpected img src $src" ;;
    esac
  done < <(grep -oP '<img[^>]+src="\K[^"]+' "$f")

  # First visible content must be the hero (if any) and then the one-liner.
  first=$(tr -d '\n' <"$f" | grep -oP '<div class="wrap">\s*<\K[^>]+' | head -1)
  [[ $first == figure\ class=\"hero\"* || $first == section\ class=\"one-liner\"* ]] || bad "first element in .wrap is <$first>"
  grep -q 'class="one-liner-text"' "$f" || bad "no one-liner panel"
done

if (( fail )); then echo "AUDIT FAILED"; exit 1; fi
echo "AUDIT PASSED"

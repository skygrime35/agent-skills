#!/usr/bin/env bash
# check-host-safety.sh — mechanical do-no-harm guardrail for /new-project.
# snapshot: record the host's pre-run state. diff: prove nothing pre-existing changed.
# Exit codes: 0 = clean, 1 = violation (block the run/checkpoint), 2 = usage error.
set -euo pipefail

MIN_DISK_KB=$((3 * 1024 * 1024))  # 3 GB floor

usage() {
  echo "usage: $0 snapshot <dir>"
  echo "       $0 diff <dir> [--allow-name <name>]... [--allow-port <port>]..."
  exit 2
}

capture() {
  local dir="$1"
  mkdir -p "$dir"
  ss -tlnp 2>/dev/null | awk 'NR>1 {print $4}' | sort -u > "$dir/listeners.txt"
  docker ps --format '{{.Names}}' 2>/dev/null | sort > "$dir/docker.txt"
  ls -1 /etc/nginx/sites-enabled 2>/dev/null | sort > "$dir/vhosts.txt"
  df --output=avail -k / | tail -1 | tr -d ' ' > "$dir/disk.txt"
}

[ $# -ge 2 ] || usage
MODE="$1"; DIR="$2"; shift 2

case "$MODE" in
  snapshot)
    capture "$DIR"
    echo "OK: snapshot written to $DIR"
    ;;
  diff)
    [ -f "$DIR/listeners.txt" ] || { echo "VIOLATION: no snapshot at $DIR — Phase 0 was skipped"; exit 1; }
    ALLOW_NAMES=(); ALLOW_PORTS=()
    while [ $# -gt 0 ]; do
      case "$1" in
        --allow-name) ALLOW_NAMES+=("$2"); shift 2 ;;
        --allow-port) ALLOW_PORTS+=("$2"); shift 2 ;;
        *) usage ;;
      esac
    done
    NOW=$(mktemp -d)
    trap 'rm -rf "$NOW"' EXIT
    capture "$NOW"
    FAIL=0

    # 1. Anything pre-existing that vanished = something was broken.
    for f in listeners docker vhosts; do
      while IFS= read -r line; do
        [ -n "$line" ] || continue
        if ! grep -qxF "$line" "$NOW/$f.txt"; then
          echo "VIOLATION: pre-existing $f entry disappeared: $line"
          FAIL=1
        fi
      done < "$DIR/$f.txt"
    done

    # 2. Anything new that isn't ours = unexpected creation.
    for f in docker vhosts; do
      while IFS= read -r line; do
        [ -n "$line" ] || continue
        grep -qxF "$line" "$DIR/$f.txt" && continue
        ok=0
        for n in "${ALLOW_NAMES[@]:-}"; do
          [ -n "$n" ] && case "$line" in *"$n"*) ok=1 ;; esac
        done
        [ "$ok" = 1 ] || { echo "VIOLATION: unexpected new $f entry: $line"; FAIL=1; }
      done < "$NOW/$f.txt"
    done
    while IFS= read -r line; do
      [ -n "$line" ] || continue
      grep -qxF "$line" "$DIR/listeners.txt" && continue
      port="${line##*:}"
      ok=0
      for p in "${ALLOW_PORTS[@]:-}"; do
        [ "$port" = "$p" ] && ok=1
      done
      [ "$ok" = 1 ] || { echo "VIOLATION: unexpected new listener: $line"; FAIL=1; }
    done < "$NOW/listeners.txt"

    # 3. Disk floor.
    AVAIL=$(cat "$NOW/disk.txt")
    if [ "$AVAIL" -lt "$MIN_DISK_KB" ]; then
      echo "VIOLATION: free disk below 3 GB floor ($((AVAIL / 1024)) MB left)"
      FAIL=1
    fi

    if [ "$FAIL" = 0 ]; then
      echo "OK: host-safety diff clean (allowed: names=${ALLOW_NAMES[*]:-none} ports=${ALLOW_PORTS[*]:-none})"
    fi
    exit "$FAIL"
    ;;
  *) usage ;;
esac

#!/usr/bin/env bash
# WebPortKit Track S: второй проход переименования — bundle/XPC ID под нас.
# Первый проход (их script_rename.sh) уже сделал com.apple.* -> com.matthewbenedict.*
# (в клоне за датой: com.apple.WebKit осталось 0, matthewbenedict — 116 файлов).
# Мы делаем com.matthewbenedict.* -> space.webportkit.* (наш неймспейс).
# Имена фреймворков/продуктов (CyberKit.framework и т.п.) НЕ трогаем — их знает build-system.
#
# Использование: wp-rename-ids.sh [count|apply] [SRC_DIR]
# apply в precious-клоне запрещён без WP_ALLOW_IN_PLACE=1.
set -euo pipefail

MODE="${1:-count}"
SRC="${2:-$(cd "$(dirname "$0")/../../artifacts/cyberkit-src/Source" && pwd)}"
FROM="com.matthewbenedict"
TO="space.webportkit"

if [ "$MODE" == "count" ]; then
  echo "files: $(rg -l "$FROM" "$SRC" 2>/dev/null | wc -l || true)"
  echo "occurrences: $(rg -o "$FROM" "$SRC" 2>/dev/null | wc -l || true)"
  echo "distinct IDs:"
  rg -o --no-filename "$FROM\.[A-Za-z0-9.]+" "$SRC" 2>/dev/null | sort -u || true
  exit 0
fi

if [ "$MODE" == "apply" ]; then
  case "$SRC" in
    *artifacts/cyberkit-src*) [ "${WP_ALLOW_IN_PLACE:-0}" == "1" ] || {
      echo "ОТКАЗ: apply в precious-клоне без WP_ALLOW_IN_PLACE=1" >&2; exit 1; } ;;
  esac
  (rg -l "$FROM" "$SRC" 2>/dev/null || true) | while read -r f; do
    perl -pi -e "s/\Q$FROM\E/$TO/g" "$f"
  done || true
  echo "apply done"
  exit 0
fi

echo "usage: $0 [count|apply] [SRC_DIR]" >&2; exit 1

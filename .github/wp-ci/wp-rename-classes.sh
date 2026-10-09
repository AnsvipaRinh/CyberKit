#!/usr/bin/env bash
# WebPortKit Track S: WP-переименование ObjC-классов донора (черновик).
# Зачем: донор CyberKit несёт классы WKWebView/WebView и др. БЕЗ переименования —
# в процессе MobileSafari они столкнутся с системным WebKit. Переименовываем на
# уровне исходников ДО сборки на CI (M5 co-load).
#
# Маппинг (без коллизий): WK* -> WP* (кроме C API *Ref), _WK* -> _WP*.
# C++/C API НЕ ломаются переименованием: все использования внутри донора
# переименовываются тем же sed (декларации+определения+вызовы), а внешних
# потребителей у приватного бандла нет. Строковые KVC/NSStringFromClass — тоже
# консистентно (это даже чинит поиск классов по имени).
#
# Использование:
#   wp-rename-classes.sh count [SRC_DIR]   — только замер (файлы/вхождения по классам)
#   wp-rename-classes.sh apply [SRC_DIR]   — замена в .m/.mm (+ .h только с --include-headers)
# По умолчанию SRC_DIR=artifacts/cyberkit-src/Source, apply в precious-клоне запрещён
# без WP_ALLOW_IN_PLACE=1 (CI делает свой checkout и правит там).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
LIST="$HERE/wp-class-rename.txt"
MODE="${1:-count}"
SRC="${2:-$HERE/../../artifacts/cyberkit-src/Source}"
WITH_HEADERS=0
[[ "${3:-}" == "--include-headers" ]] && WITH_HEADERS=1

# Построить пары OLD NEW: явные OLD=NEW из списка + ПАТТЕРНЫ, замеренные по
# исходникам (все @interface WK*/_WK*). Ручной список всех 200+ классов нереален.
pairs() {
  grep -v '^[[:space:]]*#' "$LIST" | grep -v '^[[:space:]]*$' | while read -r line; do
    line="$(echo "$line" | tr -d '[[:space:]]')"
    [ -z "$line" ] && continue
    case "$line" in
      *=*) echo "PAIR $line" | tr '=' ' ' ;;
      \!*) echo "EXCL ${line#!}" ;;
    esac
  done || true
  # Паттерн 1: все @interface/@protocol WK* (замерено: ~150 классов + ~63 протокола;
  # внутренние WKContentView/WKScrollView — тоже в ObjC runtime и тоже столкнутся).
  { rg -o '@interface (WK[A-Za-z0-9_]+)' "$SRC" --glob '*.h' -N 2>/dev/null;
    rg -o '@protocol (WK[A-Za-z0-9_]+)' "$SRC" --glob '*.h' -N 2>/dev/null; } \
    | sed 's/.*@\(interface\|protocol\) //;s/ .*//' | sort -u \
    | while read -r c; do
      case "$c" in *Ref) ;; *) echo "PATTERN $c WP${c#WK}" ;; esac
    done || true
  # Паттерн 2: все @interface/@protocol _WK* (замерено: 78 классов + делегаты).
  { rg -o '@interface (_WK[A-Za-z0-9_]+)' "$SRC" --glob '*.h' -N 2>/dev/null;
    rg -o '@protocol (_WK[A-Za-z0-9_]+)' "$SRC" --glob '*.h' -N 2>/dev/null; } \
    | sed 's/.*@\(interface\|protocol\) //;s/ .*//' | sort -u \
    | while read -r c; do echo "PATTERN $c _WP${c#_WK}"; done || true
  # WebKitLegacy Web*: явные пары (маленький закрытый набор, префикс WPL).
  for c in WebView WebFrame WebFrameView WebDataSource WebHistory WebHistoryItem \
           WebPreferences WebUIDelegate WebPolicyDelegate WebDownload WebBackForwardList; do
    echo "PATTERN $c WPL${c#Web}"
  done
}

if [ "$MODE" == "count" ]; then
  printf "%-28s %8s %8s %8s\n" "CLASS->NEW" ".mm-occ" ".m-occ" ".h-occ"
  pairs | while read -r kind old new; do
    [ "$kind" == "EXCL" ] && continue
    mm=$(rg -o "\b$old\b" "$SRC" --glob '*.mm' 2>/dev/null | wc -l || true)
    m=$(rg -o "\b$old\b" "$SRC" --glob '*.m' 2>/dev/null | wc -l || true)
    h=$(rg -o "\b$old\b" "$SRC" --glob '*.h' 2>/dev/null | wc -l || true)
    printf "%-28s %8s %8s %8s\n" "$old->$new" "$mm" "$m" "$h"
  done
  exit 0
fi

if [ "$MODE" == "apply" ]; then
  case "$SRC" in
    *artifacts/cyberkit-src*) [ "${WP_ALLOW_IN_PLACE:-0}" == "1" ] || {
      echo "ОТКАЗ: apply в precious-клоне без WP_ALLOW_IN_PLACE=1" >&2; exit 1; } ;;
  esac
  globs=(-g '*.m' -g '*.mm'); [ "$WITH_HEADERS" == "1" ] && globs+=(-g '*.h')
  pairs | while read -r kind old new; do
    [ "$kind" == "EXCL" ] && continue
    echo "rename $old -> $new"
    (rg -l "\b$old\b" "$SRC" "${globs[@]}" 2>/dev/null || true) | while read -r f; do
      perl -pi -e "s/\b$old\b/$new/g" "$f"
    done || true
  done
  exit 0
fi

echo "usage: $0 [count|apply] [SRC_DIR] [--include-headers]" >&2; exit 1

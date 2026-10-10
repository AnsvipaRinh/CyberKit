#!/usr/bin/env python3
"""WebPortKit Track S: disable readline usage in jsc.cpp for device builds.

This WebKit fork enables HAVE(READLINE) for its iOS builds, but the iPhoneOS
SDK no longer ships readline/history.h/readline.h, so jsc.cpp fails with
"'readline/history.h' file not found". Upstream jsc only uses readline on
UNIX/GTK-style hosts; neutralizing the guard keeps the iOS build clean
without changing any behaviour the CLI uses on device (no interactive
history on iOS anyway).

Idempotent. Usage: wp-jsc-compat.py <checkout-root>
"""
import io
import os
import sys

REL = "Source/CyberScriptCore/jsc.cpp"
OLD = "#if HAVE(READLINE)"
NEW = "#if 0 && HAVE(READLINE)  /* WebPortKit: readline unavailable on iOS SDK */"


def main():
    root = sys.argv[1]
    path = os.path.join(root, REL)
    if not os.path.isfile(path):
        print("  ! %s not found; nothing to do" % REL)
        return 0
    with io.open(path, "r", encoding="utf-8") as f:
        src = f.read()
    if NEW in src:
        print("  = %s already patched" % REL)
        return 0
    if OLD not in src:
        print("  ! guard anchor not found; skipping" % REL)
        return 0
    src = src.replace(OLD, NEW)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print("  + %s: readline guard neutralized" % REL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
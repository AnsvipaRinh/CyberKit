#!/usr/bin/env python3
"""WebPortKit Track S: objc/objc-runtime.h removed from modern SDKs.

Newer iPhoneOS SDKs no longer ship the legacy umbrella header
<objc/objc-runtime.h>; WebKit's JSWrapperMap.h (and possibly other files)
import it, causing "'objc/objc-runtime.h' file not found". The modern
spelling is <objc/runtime.h> (which objc-runtime.h used to forward to).

Replaces the include path everywhere under Source/**. Idempotent.
Usage: wp-objcruntime-compat.py <checkout-root>
"""
import io
import os
import sys

EXTS = (".h", ".m", ".mm", ".c", ".cpp", ".cc", ".hpp")
SKIP_DIRS = ("ThirdParty/libwebrtc", "WTF/icu", ".git")

# Legacy ObjC umbrella headers removed from modern SDKs -> modern spelling.
LEGACY_MAP = {
    "objc/objc-runtime.h": "objc/runtime.h",
    "objc/Protocol.h": "objc/runtime.h",
    "objc/objc-class.h": "objc/runtime.h",
    "objc/objc-object.h": "objc/runtime.h",
}


def main():
    root = sys.argv[1]
    changed = 0
    for dirpath, dirnames, filenames in os.walk(os.path.join(root, "Source")):
        rel_dir = os.path.relpath(dirpath, root)
        if any(skip in rel_dir for skip in SKIP_DIRS):
            continue
        for name in filenames:
            if not name.endswith(EXTS):
                continue
            path = os.path.join(dirpath, name)
            try:
                with io.open(path, "r", encoding="utf-8", errors="ignore") as f:
                    src = f.read()
            except OSError:
                continue
            out = src
            for legacy, modern in LEGACY_MAP.items():
                for kw in ("import", "include"):
                    src_line = "#%s <%s>" % (kw, legacy)
                    if src_line in out:
                        out = out.replace(src_line, "#%s <%s>" % (kw, modern))
            if out != src:
                with io.open(path, "w", encoding="utf-8") as f:
                    f.write(out)
                changed += 1
                print("  + %s: legacy ObjC includes fixed" % os.path.relpath(path, root))
    if not changed:
        print("  = objc-runtime includes already clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
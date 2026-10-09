#!/usr/bin/env python3
"""WebPortKit Track S: repoint /usr/lib/libSystem.B.dylib build inputs at the SDK.

WebKit's libwebrtc.xcodeproj hardcodes /usr/lib/libSystem.B.dylib in OTHER_LDFLAGS.
On macOS 11+ those dylibs only exist in the dyld shared cache, so Xcode fails the
libwebrtc target with:
    Build input file cannot be found: /usr/lib/libSystem.B.dylib

Fix (as upstream WebKit did): address it relative to the SDK root, quoted:
    /usr/lib/libSystem.B.dylib  ->  "$(SDKROOT)/usr/lib/libSystem.B.dylib"

Idempotent. Usage: wp-libwebrtc-compat.py <checkout-root>
"""
import re
import sys
import os
import io

TARGET = os.path.join("Source", "ThirdParty", "libwebrtc", "libwebrtc.xcodeproj",
                      "project.pbxproj")


def main():
    root = sys.argv[1]
    path = os.path.join(root, TARGET)
    if not os.path.isfile(path):
        print("  ! %s not found; nothing to do" % TARGET)
        return 0
    with io.open(path, "r", encoding="utf-8") as f:
        src = f.read()

    had_bare = re.search(r"\t/usr/lib/libSystem\.B\.dylib", src) is not None

    if had_bare:
        # pbxproj array elements with variables must be quoted.
        src = re.sub(
            r"^(\t+)/usr/lib/libSystem\.B\.dylib(,?)$",
            r'\1"$(SDKROOT)/usr/lib/libSystem.B.dylib"\2',
            src, flags=re.M)

    if had_bare:
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(src)
        print("  + %s: libSystem.B.dylib now \u0024(SDKROOT)-relative (quoted)" % TARGET)
    else:
        print("  = %s already patched" % TARGET)
    return 0


if __name__ == "__main__":
    sys.exit(main())
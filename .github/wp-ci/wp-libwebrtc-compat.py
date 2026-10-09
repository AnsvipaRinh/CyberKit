#!/usr/bin/env python3
"""WebPortKit Track S: repoint /usr/lib/libSystem.B.dylib build inputs at the SDK.

WebKit's libwebrtc.xcodeproj hardcodes /usr/lib/libSystem.B.dylib in OTHER_LDFLAGS.
On macOS 11+ those system dylibs only exist in the dyld shared cache, so Xcode
fails the libwebrtc target with:
    Build input file cannot be found: /usr/lib/libSystem.B.dylib

Fix used upstream: address it relative to the SDK root:
    /usr/lib/libSystem.B.dylib  ->  $(SDKROOT)/usr/lib/libSystem.B.dylib

Idempotent. Usage: wp-libwebrtc-compat.py <checkout-root>
"""
import sys
import os
import io

TARGET = os.path.join("Source", "ThirdParty", "libwebrtc", "libwebrtc.xcodeproj",
                      "project.pbxproj")

OLD = "/usr/lib/libSystem.B.dylib"
NEW = "$(SDKROOT)/usr/lib/libSystem.B.dylib"


def main():
    root = sys.argv[1]
    path = os.path.join(root, TARGET)
    if not os.path.isfile(path):
        print("  ! %s not found; nothing to do" % TARGET)
        return 0
    with io.open(path, "r", encoding="utf-8") as f:
        src = f.read()

    # Idempotency: if the SDK-relative spelling is already there, do nothing.
    if NEW in src and OLD.replace("/usr/", "$(SRCROOT)/../usr/") not in src:
        # still allow the plain spelling to be rewritten when mixed
        pass
    if "$(SDKROOT)/usr/lib/libSystem.B.dylib" in src and \
            "\n\t\t\t\t\t/usr/lib/libSystem.B.dylib" not in src:
        print("  = %s already patched" % TARGET)
        return 0

    count = src.count("\t" + OLD + ",\n")  # tab-indented occurrences as in pbxproj
    if count:
        src = src.replace("\t" + OLD + ",\n", "\t" + NEW + ",\n")
    count2 = src.count("\t\t\t\t/usr/lib/libSystem.B.dylib\n")
    if count2:
        src = src.replace("\t\t\t\t/usr/lib/libSystem.B.dylib\n", "\t\t\t\t" + NEW + "\n")

    if src.count("\t\t\t\t/usr/lib/libSystem.B.dylib") == 0 and \
       src.rstrip().endswith(OLD + ","):
        pass
    remaining = [l for l in src.splitlines() if l.strip() == OLD]
    if remaining:
        for line in remaining:
            src = src.replace(line, line.replace(OLD, NEW))

    if OLD not in src.replace(NEW, "___PLACEHOLDER___"):
        pass
    # Final safety net: any *remaining* bare occurrence gets rewritten once,
    # but never rewrite inside an existing $(SDKROOT)-prefixed path twice.
    out_lines = []
    for line in src.splitlines(True):
        if OLD in line and NEW not in line:
            line = line.replace(OLD, NEW)
        out_lines.append(line)
    src = "".join(out_lines)

    with io.open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print("  + %s: libSystem.B.dylib now SDK-relative" % TARGET)
    return 0


if __name__ == "__main__":
    sys.exit(main())
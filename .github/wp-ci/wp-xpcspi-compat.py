#!/usr/bin/env python3
"""WebPortKit Track S: make 2023-era vendored WTF XPC SPI declarations coexist
with modern Apple SDKs (>= iOS 16.4 / macOS 13.3 SDK ship xpc/activity.h with
XPC_ACTIVITY_STATE_* + xpc_*_t as real structs). Without this guard the
iPhoneOS 17.5 SDK build fails in WTF with "redefinition of enumerator
XPC_ACTIVITY_STATE_*" and "typedef redefinition" errors.

Idempotent: re-running is a no-op (anchors are replaced with themselves).

Usage: wp-xpcspi-compat.py <checkout-root>
"""
import sys
import os
import io

TARGET = os.path.join("Source", "WTF", "wtf", "spi", "darwin", "XPCSPI.h")

SDK_BRANCH_OLD = """#if PLATFORM(MAC) || USE(APPLE_INTERNAL_SDK)
#include <xpc/xpc.h>
#else
"""

SDK_BRANCH_NEW = """#if PLATFORM(MAC) || USE(APPLE_INTERNAL_SDK)
#include <xpc/xpc.h>
#elif defined(__has_include) && __has_include(<xpc/activity.h>)
// Modern SDKs (iOS 16.4+/macOS 13.3+ SDK) ship the full vendored XPC SPI
// (xpc/activity.h with XPC_ACTIVITY_STATE_*, xpc_*_t as real structs,
// OS_OBJECT_DECL support for xpc_object). Using the SDK spelling avoids the
// duplicate-protocol/duplicate-enumerator/typedef-redefinition errors.
#include <xpc/xpc.h>
#else
"""

ENUM_GUARD_OLD = """enum {
    XPC_ACTIVITY_STATE_CHECK_IN,
    XPC_ACTIVITY_STATE_WAIT,
    XPC_ACTIVITY_STATE_RUN,
    XPC_ACTIVITY_STATE_DEFER,
    XPC_ACTIVITY_STATE_CONTINUE,
    XPC_ACTIVITY_STATE_DONE,
};
typedef long xpc_activity_state_t;"""

ENUM_GUARD_NEW = """#if !defined(__has_include)
#define __has_include(x) 0
#endif
#if !__has_include(<xpc/activity.h>)
enum {
    XPC_ACTIVITY_STATE_CHECK_IN,
    XPC_ACTIVITY_STATE_WAIT,
    XPC_ACTIVITY_STATE_RUN,
    XPC_ACTIVITY_STATE_DEFER,
    XPC_ACTIVITY_STATE_CONTINUE,
    XPC_ACTIVITY_STATE_DONE,
};
typedef long xpc_activity_state_t;
#endif"""


def main():
    root = sys.argv[1]
    path = os.path.join(root, TARGET)
    if not os.path.isfile(path):
        print("  ! %s not found; nothing to do" % TARGET)
        return 0
    with io.open(path, "r", encoding="utf-8") as f:
        src = f.read()
    changed = False

    # 1. SDK branch: when the SDK ships the XPC SPI, use it wholesale instead
    #    of the vendored block (which now collides with the SDK's ObjC
    #    protocol form on new toolchains).
    if "elif defined(__has_include) && __has_include(<xpc/activity.h>)" not in src:
        if SDK_BRANCH_OLD not in src:
            print("  ! SDK-branch anchor not found; skipping (already patched?)")
        else:
            src = src.replace(SDK_BRANCH_OLD, SDK_BRANCH_NEW)
            changed = True

    # 2. Legacy fallback enum for old SDKs only.
    if "#if !__has_include(<xpc/activity.h>)" not in src:
        if ENUM_GUARD_OLD not in src:
            print("  ! enum anchor not found; skipping (already patched?)")
        else:
            src = src.replace(ENUM_GUARD_OLD, ENUM_GUARD_NEW)
            changed = True

    if changed:
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(src)
        print("  + %s patched (SDK-provided xpc/activity.h wins)" % TARGET)
    else:
        print("  = %s already patched" % TARGET)
    return 0


if __name__ == "__main__":
    sys.exit(main())
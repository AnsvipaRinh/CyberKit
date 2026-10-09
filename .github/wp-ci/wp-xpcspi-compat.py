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

HAS_INCLUDE_GUARD = """#if !defined(__has_include)
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

ENUM_ORIGINAL = """enum {
    XPC_ACTIVITY_STATE_CHECK_IN,
    XPC_ACTIVITY_STATE_WAIT,
    XPC_ACTIVITY_STATE_RUN,
    XPC_ACTIVITY_STATE_DEFER,
    XPC_ACTIVITY_STATE_CONTINUE,
    XPC_ACTIVITY_STATE_DONE,
};
typedef long xpc_activity_state_t;"""

VOID_TYPEDEFS_ORIGINAL = """#else // OS_OBJECT_USE_OBJC

typedef void* xpc_object_t;
typedef void* xpc_connection_t;
typedef void* xpc_endpoint_t;
typedef void* xpc_activity_t;

#define XPC_GLOBAL_OBJECT(object) (&(object))

#endif // OS_OBJECT_USE_OBJC"""

VOID_TYPEDEFS_NEW = """#elif !defined(__has_include) || !__has_include(<xpc/activity.h>)

typedef void* xpc_object_t;
typedef void* xpc_connection_t;
typedef void* xpc_endpoint_t;
typedef void* xpc_activity_t;

#define XPC_GLOBAL_OBJECT(object) (&(object))

#endif // OS_OBJECT_USE_OBJC"""


def main():
    root = sys.argv[1]
    path = os.path.join(root, TARGET)
    if not os.path.isfile(path):
        print("  ! %s not found; nothing to do" % TARGET)
        return 0
    with io.open(path, "r", encoding="utf-8") as f:
        src = f.read()
    changed = False

    if "!__has_include(<xpc/activity.h>)\nenum {" not in src:
        if ENUM_ORIGINAL not in src:
            print("  ! enum anchor not found; skipping (already patched?)")
        else:
            src = src.replace(ENUM_ORIGINAL, HAS_INCLUDE_GUARD)
            changed = True

    if VOID_TYPEDEFS_NEW not in src:
        if VOID_TYPEDEFS_ORIGINAL not in src:
            print("  ! os-object anchor not found; skipping (already patched?)")
        else:
            src = src.replace(VOID_TYPEDEFS_ORIGINAL, VOID_TYPEDEFS_NEW)
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
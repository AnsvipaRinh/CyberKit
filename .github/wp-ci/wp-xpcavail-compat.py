#!/usr/bin/env python3
"""WebPortKit Track S: clear SDK "unavailable" annotation on private XPC SPI use.

iOS 16.4+ SDKs declare private XPC SPI (e.g. xpc_connection_create_mach_service)
with __API_UNAVAILABLE for iOS, so WebKit's Inspector code that calls it fails
with "'xpc_connection_create_mach_service' is unavailable: not available on iOS".

Fix (standard for unavailable-but-private symbols): an unannotated
redeclaration clears the availability inherited from earlier declarations.

Idempotent. Usage: wp-xpcavail-compat.py <checkout-root>
"""
import io
import os
import sys

FILES = [
    "Source/CyberScriptCore/inspector/remote/cocoa/RemoteInspectorCocoa.mm",
    "Source/CyberScriptCore/inspector/remote/cocoa/RemoteInspectorXPCConnection.mm",
    "Source/CyberScriptCore/inspector/remote/cocoa/RemoteInspectorManager.mm",
]

REDECLS = [
    'extern "C" xpc_connection_t xpc_connection_create_mach_service(const char *name, dispatch_queue_t targetq);',
    'extern "C" void xpc_connection_set_event_handler(xpc_connection_t connection, xpc_handler_t handler);',
]

USE_SYMBOLS = [
    "xpc_connection_create_mach_service(",
    "xpc_connection_set_event_handler(",
]

BLOCK = """#if defined(__has_include) && __has_include(<xpc/activity.h>)
%s
#endif
"""


def main():
    root = sys.argv[1]
    for rel in FILES:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            print("  ! %s not found; nothing to do" % rel)
            continue
        with io.open(path, "r", encoding="utf-8") as f:
            src = f.read()

        needs = []
        for sym, redecl in zip(USE_SYMBOLS, REDECLS):
            if redecl in src:
                continue
            if sym in src:
                needs.append(redecl)

        if needs:
            block = BLOCK % "\n".join(needs)
            # insert before the first use of the first missing symbol.
            anchor = None
            for sym in USE_SYMBOLS:
                pos = src.find(sym)
                if pos >= 0 and (anchor is None or pos < anchor):
                    anchor = pos
            bol = src.rfind("\n", 0, anchor) + 1
            src = src[:bol] + block + src[bol:]
            with io.open(path, "w", encoding="utf-8") as f:
                f.write(src)
            print("  + %s: availability-cleared redeclarations added (%d)" % (rel, len(needs)))
        else:
            print("  = %s already patched (or no use site)" % rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
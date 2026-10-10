#!/usr/bin/env python3
"""WebPortKit Track S: clear SDK "unavailable" annotation on private XPC SPI.

iOS 16.4+ SDKs declare private XPC SPI with __API_UNAVAILABLE for iOS, so
WebKit's Inspector code that calls it fails with e.g.
    'xpc_connection_create_mach_service' is unavailable: not available on iOS

A plain re-declaration without availability clears the attribute inherited
from the SDK header. Signatures are copied verbatim from WTF's vendored
XPCSPI.h so they remain compatible with the call sites.

Declarations are inserted at file scope (after the last #include/#import) —
a declaration inside a function body is legal but placement-sensitive, so
top-of-file is both safe and readable.

Idempotent. Usage: wp-xpcavail-compat.py <checkout-root>
"""
import io
import os
import re
import sys

FILES = [
    "Source/CyberScriptCore/inspector/remote/cocoa/RemoteInspectorCocoa.mm",
    "Source/CyberScriptCore/inspector/remote/cocoa/RemoteInspectorXPCConnection.mm",
]

REDECLS = [
    "xpc_connection_create_mach_service",
    "xpc_connection_set_event_handler",
]

DECLS = {
    "xpc_connection_create_mach_service":
        "extern \"C\" xpc_connection_t xpc_connection_create_mach_service(const char* name, dispatch_queue_t, uint64_t flags);",
    "xpc_connection_set_event_handler":
        "extern \"C\" void xpc_connection_set_event_handler(xpc_connection_t, xpc_handler_t);",
}

GUARD_OPEN = "#if defined(__has_include) && __has_include(<xpc/activity.h>)"

COMMENT = """// WebPortKit Track S: modern Apple SDKs mark private XPC SPI as unavailable
// on iOS while WebKit still uses it; an unannotated redeclaration clears
// the availability inherited from the SDK header.
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

        missing = [s for s in REDECLS
                   if DECLS[s] not in src and (s + "(") in src]
        if not missing:
            print("  = %s already patched (or no use site)" % rel)
            continue

        # Insert at file scope: after the last #include or #import line.
        matches = list(re.finditer(r"^\s*#[ \t]*(?:import|include)\b.*$", src,
                                   flags=re.M))
        pos = matches[-1].end() if matches else 0

        block = COMMENT + GUARD_OPEN + "\n" + "\n".join(DECLS[s] for s in missing) + "\n#endif\n"
        src = src[:pos] + "\n" + block + src[pos:]
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(src)
        print("  + %s: file-scope redeclarations added (%d)" % (rel, len(missing)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
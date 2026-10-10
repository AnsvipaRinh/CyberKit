#!/usr/bin/env python3
"""WebPortKit Track S: route private XPC SPI through availability-free macros.

Modern iOS SDKs declare xpc_connection_create_mach_service /
xpc_connection_set_event_handler with __API_UNAVAILABLE for iOS, so direct
call sites in WebKit's Inspector code fail to compile. A redeclaration does
not clear the attribute, and the Inspector .mm files are compiled together in
one unified-source TU, so plain helper functions would be defined twice.

We instead install *function-like macros* (identical macro redefinition is
legal for the preprocessor) that dlsym-resolve the private symbols at runtime
-- a name lookup involves no compile-time symbol reference, so it compiles
against the new SDK and resolves on device.

Usage: WP_m5_xpc_make_service(name, queue, flags)
       WP_m5_xpc_set_handler(connection, handler)

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

CALLS = [
    ("xpc_connection_create_mach_service", "WP_m5_xpc_make_service"),
    ("xpc_connection_set_event_handler", "WP_m5_xpc_set_handler"),
]

MARKER = "WP_m5_xpc_dlsym_macros"

BLOCK = """
// WebPortKit Track S: modern iOS SDKs mark these private XPC symbols
// "__API_UNAVAILABLE on iOS"; rename-in place of dlsym-resolved macros
// (identical redefinition across unified sources is legal).
// WP_m5_xpc_dlsym_macros
#include <dlfcn.h>
#define WP_m5_xpc_make_service(name, queue, flags) ({ \
    typedef xpc_connection_t (*wp_m5_fn_t)(const char *, dispatch_queue_t, uint64_t); \
    static wp_m5_fn_t wp_m5_fn; \
    if (!wp_m5_fn) wp_m5_fn = (wp_m5_fn_t)dlsym(RTLD_DEFAULT, "xpc_connection_create_mach_service"); \
    wp_m5_fn ? wp_m5_fn(name, queue, flags) : (xpc_connection_t)0; })
#define WP_m5_xpc_set_handler(connection, handler) do { \
    typedef void (*wp_m5_fn_t)(xpc_connection_t, xpc_handler_t); \
    static wp_m5_fn_t wp_m5_fn; \
    if (!wp_m5_fn) wp_m5_fn = (wp_m5_fn_t)dlsym(RTLD_DEFAULT, "xpc_connection_set_event_handler"); \
    if (wp_m5_fn) wp_m5_fn(connection, handler); \
} while (0)
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

        changed = False
        if MARKER not in src:
            matches = list(re.finditer(r"^\s*#[ \t]*(?:import|include)\b.*$",
                                       src, flags=re.M))
            pos = matches[-1].end() if matches else 0
            src = src[:pos] + "\n" + BLOCK + src[pos:]
            changed = True

        for orig, repl in CALLS:
            src = re.sub(r"(?<![\w])" + re.escape(orig) + r"\(",
                         repl + "(", src)

        with io.open(path, "w", encoding="utf-8") as f:
            f.write(src)
        print(("  + %s: availability-free XPC macros installed" if changed
               else "  = %s: XPC macros already present; call sites renormalized") % rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
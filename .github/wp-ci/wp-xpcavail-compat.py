#!/usr/bin/env python3
"""WebPortKit Track S: route private XPC SPI calls through dlsym.

Modern iOS SDKs mark xpc_connection_create_mach_service /
xpc_connection_set_event_handler as unavailable for iOS, so direct call sites
in WebKit's Inspector code fail to compile. Redeclaring does not clear the
availability attribute, but taking the address of the symbol by NAME at
runtime via dlsym involves no compile-time symbol reference, so it compiles
against the new SDK and resolves the private function on device.

Only the two Inspector TUs that use the SPI are patched; the vendored
XPCSPI.h declarations remain untouched (declarations are not errors).

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

HELPER_MARKER = "WP_m5_xpc_dlsym_helpers"

HELPERS = """
// WebPortKit Track S: private XPC SPI marked __API_UNAVAILABLE by modern SDKs.
// Resolve the symbols at runtime by name (no compile-time reference).
// WP_m5_xpc_dlsym_helpers
#include <dlfcn.h>
static inline xpc_connection_t WP_m5_xpc_make_service(const char *name, dispatch_queue_t queue, uint64_t flags)
{
    typedef xpc_connection_t (*fn_t)(const char *, dispatch_queue_t, uint64_t);
    static fn_t fn;
    if (!fn) fn = (fn_t)dlsym(RTLD_DEFAULT, "xpc_connection_create_mach_service");
    return fn ? fn(name, queue, flags) : nullptr;
}
static inline void WP_m5_xpc_set_handler(xpc_connection_t connection, xpc_handler_t handler)
{
    typedef void (*fn_t)(xpc_connection_t, xpc_handler_t);
    static fn_t fn;
    if (!fn) fn = (fn_t)dlsym(RTLD_DEFAULT, "xpc_connection_set_event_handler");
    if (fn) fn(connection, handler);
}
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
        if HELPER_MARKER not in src:
            matches = list(re.finditer(r"^\s*#[ \t]*(?:import|include)\b.*$",
                                       src, flags=re.M))
            pos = matches[-1].end() if matches else 0
            src = src[:pos] + "\n" + HELPERS + src[pos:]
            changed = True

        for orig, repl in CALLS:
            src = re.sub(r"(?<![\w])" + re.escape(orig) + r"\(",
                         repl + "(", src)
            if repl not in src:
                print("  ! %s: call site for %s not found" % (rel, orig))

        if changed or True:
            with io.open(path, "w", encoding="utf-8") as f:
                f.write(src)
            print("  + %s: XPC SPI calls routed through dlsym helpers" % rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
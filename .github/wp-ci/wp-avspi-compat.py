#!/usr/bin/env python3
"""WebPortKit Track S: guard vendored AVFoundation SPI that the iOS 17 SDK exposes.

WTF's vendored PAL/spi/cocoa/AVFoundationSPI.h declares, among others,
'@interface AVVideoPerformanceMetrics : NSObject' unconditionally when not
building against the internal SDK. The iOS 17.4+ SDK exposes this private
interface publicly, producing:
    error: duplicate interface definition for class 'AVVideoPerformanceMetrics'

Fix (upstream-style): only compile the vendored definition when building
against an SDK older than iOS 17. Newer SDKs provide the interface (and, in
newer SDKs, its newer properties) themselves.

Idempotent. Usage: wp-avspi-compat.py <checkout-root>
"""
import io
import os
import sys

REL = "Source/CyberCore/PAL/pal/spi/cocoa/AVFoundationSPI.h"

OLD = "#if !USE(APPLE_INTERNAL_SDK)\n@interface AVVideoPerformanceMetrics : NSObject"
NEW = ("#if !USE(APPLE_INTERNAL_SDK) && "
       "(!defined(__IPHONE_OS_VERSION_MAX_ALLOWED) || __IPHONE_OS_VERSION_MAX_ALLOWED < 170000)\n"
       "@interface AVVideoPerformanceMetrics : NSObject")

# The internal-SDK #else branch (category adding DisplayComposited properties)
# must be guarded too: on iOS 17.4+ SDK the class is API_AVAILABLE(ios(17.4)),
# which fails under -Werror,-Wunguarded-availability-new.
CATEGORY = """#else
@interface AVVideoPerformanceMetrics (AVVideoPerformanceMetricsDisplayCompositedVideoFrames)
@property (nonatomic, readonly) unsigned long numberOfDisplayCompositedVideoFrames;
@property (nonatomic, readonly) unsigned long numberOfNonDisplayCompositedVideoFrames;
@end
#endif
"""
CATEGORY_GUARDED = """#elif (!defined(__IPHONE_OS_VERSION_MAX_ALLOWED) || __IPHONE_OS_VERSION_MAX_ALLOWED < 170000)
@interface AVVideoPerformanceMetrics (AVVideoPerformanceMetricsDisplayCompositedVideoFrames)
@property (nonatomic, readonly) unsigned long numberOfDisplayCompositedVideoFrames;
@property (nonatomic, readonly) unsigned long numberOfNonDisplayCompositedVideoFrames;
@end
#endif
#endif
"""

# Sanity anchors that must remain present after patching.
ANCHORS = [
    "@property (nonatomic, readonly) double totalFrameDelay;",
    "@interface AVSampleBufferDisplayLayer (CyberCorePrivate)",
]


def main():
    root = sys.argv[1]
    path = os.path.join(root, REL)
    if not os.path.isfile(path):
        print("  ! %s not found; nothing to do" % REL)
        return 0
    with io.open(path, "r", encoding="utf-8") as f:
        src = f.read()

    if "__IPHONE_OS_VERSION_MAX_ALLOWED < 170000)" in src:
        print("  = %s already patched" % REL)
        return 0
    if OLD not in src:
        print("  ! %s: AVVideoPerformanceMetrics anchor not found" % REL)
        return 0

    src = src.replace(OLD, NEW, 1)
    if CATEGORY in src:
        src = src.replace(CATEGORY, CATEGORY_GUARDED, 1)
    else:
        print("  ! %s: category branch anchor not found" % REL)
        return 1

    for a in ANCHORS:
        if a not in src:
            print("  ! %s: anchor missing after patch: %s" % (REL, a[:60]))
            return 1

    with io.open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print("  + %s: AVVideoPerformanceMetrics vendored decl guarded to SDK < 17" % REL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
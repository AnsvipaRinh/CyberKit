#!/usr/bin/env python3
"""WebPortKit Track S: make WebKit's Ruby helper scripts work on Ruby >= 3.2.

GitHub's macOS runners ship Homebrew Ruby 3.x where `File.exists?` and
`Dir.exists?` were removed (they were deprecated aliases of `File.exist?` /
`Dir.exist?`). WebKit's Tools/Scripts/* call the old names, so the build dies in
a "Check For Inappropriate Macros in External Headers" phase with:

    undefined method `exists?' for class File (NoMethodError)

Fix: rewrite the deprecated aliases in the repo's Ruby scripts. Behaviour is
identical (the old names were aliases of the new ones).

Idempotent. Usage: wp-ruby-compat.py <checkout-root>
"""
import io
import os
import re
import sys

REPLACEMENTS = [
    (re.compile(r"\bFile\.exists\?"), "File.exist?"),
    (re.compile(r"\bDir\.exists\?"), "Dir.exist?"),
]

SKIP_DIRS = {".git", "WebKitBuild", "DerivedSources", "node_modules"}


def ruby_files(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            full = os.path.join(base, f)
            if f.endswith(".rb") or f.endswith(".gemspec") or f == "Rakefile":
                yield full
                continue
            # WebKit's Tools/Scripts helpers have NO extension at all and start
            # with a ruby shebang (e.g. check-for-inappropriate-macros-in-external-headers).
            if "." not in f:
                try:
                    with io.open(full, "r", encoding="utf-8") as fh:
                        if "ruby" in fh.readline().lower():
                            yield full
                except (UnicodeDecodeError, OSError):
                    pass


def main():
    root = sys.argv[1]
    changed = 0
    scanned = 0
    for path in ruby_files(root):
        scanned += 1
        try:
            with io.open(path, "r", encoding="utf-8") as fh:
                src = fh.read()
        except (UnicodeDecodeError, OSError):
            continue
        new = src
        for pattern, repl in REPLACEMENTS:
            new = pattern.sub(repl, new)
        if new != src:
            with io.open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
            changed += 1
            print("  + %s" % os.path.relpath(path, root))
    print("  = wp-ruby-compat: %d ruby files scanned, %d patched" % (scanned, changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
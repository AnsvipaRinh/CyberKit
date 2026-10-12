#!/bin/zsh

# WebPortKit Track S: rename bundle identifiers from com.matthewbenedict.* to space.webportkit.*
# This script renames CFBundleIdentifier and related strings in Info.plist files.

PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

if [ -x /opt/homebrew/bin/rename ]; then
    echo "Found /opt/homebrew/bin/rename"
elif [ -x /usr/local/bin/rename ]; then
    echo "Found /usr/local/bin/rename"
else
    echo "Please install rename with Homebrew"
    exit 1
fi

# Rename contents of files
echo $'(1/17) Replacing com.matthewbenedict.${PRODUCT_NAME:rfc1034identifier}'
LC_ALL=C git grep -lz $'com\.apple\.\$\{PRODUCT_NAME:rfc1034identifier\}' . | xargs -0 gsed -i $'s|com\.apple\.\$\{PRODUCT_NAME:rfc1034identifier\}|space.webportkit.\${PRODUCT_NAME:rfc1034identifier}|g'

echo $'(5/17) Replacing com.apple.${PRODUCT_NAME:rfc1034identifier}'
LC_ALL=C git grep -lz $'com\.apple\.\$\{PRODUCT_NAME:rfc1034identifier\}' . | xargs -0 gsed -i $'s|com\.apple\.\$\{PRODUCT_NAME:rfc1034identifier\}|space.webportkit.\${PRODUCT_NAME:rfc1034identifier}|g'

# Fix bundle identifiers
echo $'(6/17) Replacing com.apple.CyberScriptCore'
LC_ALL=C git grep -lz $'com\.apple\.CyberScriptCore' . | xargs -0 gsed -i $'s|com\.apple\.CyberScriptCore|space.webportkit.CyberScriptCore|g'
echo $'(7/17) Replacing com.apple.CyberCore'
LC_ALL=C git grep -lz $'com\.apple\.CyberCore' . | xargs -0 gsed -i $'s|com\.apple\.CyberCore|space.webportkit.CyberCore|g'
echo $'(8/17) Replacing com.apple.CyberKitLegacy'
LC_ALL=C git grep -lz $'com\.apple\.CyberKitLegacy' . | xargs -0 gsed -i $'s|com\.apple\.CyberKitLegacy|space.webportkit.CyberKitLegacy|g'
echo $'(9/17) Replacing com.apple.CyberKit'
LC_ALL=C git grep -lz $'com\.apple\.CyberKit' . | xargs -0 gsed -i $'s|com\.apple\.CyberKit|space.webportkit.CyberKit|g'

# Rename some actual files
echo $'(10/17) Renaming com.apple.CyberScriptCore'
find . -name $'*com\.apple\.CyberScriptCore*' -exec rename $'s|com\.apple\.CyberScriptCore|space.webportkit.CyberScriptCore|g' {} \;
echo $'(11/17) Renaming com.apple.CyberCore'
find . -name $'*com\.apple\.CyberCore*' -exec rename $'s|com\.apple\.CyberCore|space.webportkit.CyberCore|g' {} \;
echo $'(12/17) Renaming com.apple.CyberKitLegacy'
find . -name $'*com\.apple\.CyberKitLegacy*' -exec rename $'s|com\.apple\.CyberKitLegacy|space.webportkit.CyberKitLegacy|g' {} \;
echo $'(13/17) Renaming com.apple.CyberKit'
find . -name $'*com\.apple\.CyberKit*' -exec rename $'s|com\.apple\.CyberKit|space.webportkit.CyberKit|g' {} \;

# Because the files are renamed, the CyberKit equivalents are correct here
echo $'(14/17) Renaming com.apple.CyberScriptCore'
find . -name $'*com\.apple\.CyberScriptCore*' -exec rename $'s|com\.apple\.CyberScriptCore|space.webportkit.CyberScriptCore|g' {} \;
echo $'(15/17) Renaming com.apple.CyberCore'
find . -name $'*com\.apple\.CyberCore*' -exec rename $'s|com\.apple\.CyberCore|space.webportkit.CyberCore|g' {} \;
echo $'(16/17) Renaming com.apple.CyberKitLegacy'
find . -name $'*com\.apple\.CyberKitLegacy*' -exec rename $'s|com\.apple\.CyberKitLegacy|space.webportkit.CyberKitLegacy|g' {} \;
echo $'(17/17) Renaming com.apple.CyberKit'
find . -name $'*com\.apple\.CyberKit*' -exec rename $'s|com\.apple\.CyberKit|space.webportkit.CyberKit|g' {} \;

# Update git to track this
git add *
#!/bin/zsh

#
# Author: Kevin Griffin
#
# Disclaimer: This script is provided "as is" without warranty of any kind, either express or implied,
# including but not limited to the implied warranties of merchantability and fitness for a particular purpose.
# Use this script at your own risk. The author shall not be held responsible for any damages arising from
# the use of this script.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Requires the following environment variables to be set:
# APP_ID: The app identifier (e.g., com.example.wallet)
# DEVELOPER_ID_APP_CERT: The Developer ID Application certificate to sign the app with


if [ -z "$APP_ID" ]; then
    echo "APP_ID environment variable not set"
    exit 1
fi

if [ -z "$DEVELOPER_ID_APP_CERT" ]; then
    echo "DEVELOPER_ID_APP_CERT environment variable not set"
    exit 1
fi

if [ -z "$WALLET_ENVIRONMENT" ]; then
    echo "WALLET_ENVIRONMENT environment variable not set"
    echo "Using PRODUCTION"
    echo "Press Enter to continue..."
    WALLET_ENVIRONMENT=production
    read
else
    echo "Using $WALLET_ENVIRONMENT environment"
fi

APP_NAME="wallet"
APP_DISPLAY_NAME="Wallet"
APP_IDENTIFIER="$APP_ID"
APP_ICON="AppIcon"
APP_VERSION="0.1.0"
BUILD_DIR="build/macos"
DMG_NAME="$APP_NAME.dmg"
KC_PROFILE="org.gleif.sparan"
MACHINE_OS=$(sw_vers -buildVersion) # Get the build machine OS build version
WORKING_DIR=$(pwd)

# Create Info.plist - this is the app's metadata
echo "Creating Info.plist..."
cat <<EOF > "$BUILD_DIR/$APP_NAME.app/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- App name and icon -->
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$APP_DISPLAY_NAME</string>
    <key>CFBundleIconFile</key>
    <string>$APP_ICON</string>
    <key>CFBundleIconName</key>
    <string>$APP_ICON</string>

    <!-- App bundle ID and version -->
    <key>CFBundleIdentifier</key>
    <string>$APP_IDENTIFIER</string>
    <key>CFBundleVersion</key>
    <string>$APP_VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$APP_VERSION</string>

    <!-- App build machine, build settings, and supported platform settings -->
    <key>BuildMachineOSBuild</key>
    <string>$MACHINE_OS</string>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSupportedPlatforms</key>
    <array>
      <string>MacOSX</string>
    </array>

    <!-- App sandboxing settings -->
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>

    <!-- App environment variables -->
    <key>LSEnvironment</key>
     <dict>
       <key>WALLET_ENVIRONMENT</key>
       <string>$WALLET_ENVIRONMENT</string>
     </dict>
</dict>
</plist>
EOF

# Create entitlements.plist - this is the app's sandboxing settings
# This is required for the app to be granted permissions to access system resources on target systems
echo "Creating entitlements.plist..."
cat <<EOF > "entitlements.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.allow-dyld-environment-variables</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.network.server</key>
    <true/>
    <key>com.apple.security.device.audio-input</key>
    <true/>
    <key>com.apple.security.device.camera</key>
    <true/>
    <key>com.apple.security.device.microphone</key>
    <true/>
</dict>
</plist>
EOF


# Signing
#  - To pass the notary build we must sign the following three sets of files:
#    1. The Flutter assets in the app bundle
#    2. The Flet executable and its dependent framework executables
#    3. The app bundle itself
#  - Must sign all .so and .dylib files
#  This allows the app to be notarized by Apple and pass the MacOS Gatekeeper for non-Mac App Store distribution

# Unpack, sign, and repack Flutter assets
function sign_flutter_assets_package() {
  # Unpack, sign, and repack the zip file within the framework
  echo "Signing Flutter assets..."
  set -xe
  cd "$BUILD_DIR/$APP_NAME.app/Contents/Frameworks/App.framework/Versions/A/Resources/flutter_assets/app/" || exit 1
  set +xe
  echo "Extracting Flutter assets..."
  unzip -q app.zip -d tmp

  # Remove extended attributes from the flutter_assets
  echo "Clearing extended attributes from Flutter assets..."
  find "tmp" -type f -exec xattr -c {} \;

  # Sign the nested flet-macos.tar.gz inside .venv if it exists
  FLET_TAR_PATH="tmp/.venv/lib/python3.12/site-packages/flet_desktop/app/flet-macos.tar.gz"
  if [ -f "$FLET_TAR_PATH" ]; then
    echo "Signing nested Flet package in .venv..."
    mkdir -p flet_tmp
    tar -xzf "$FLET_TAR_PATH" -C flet_tmp

    # Remove extended attributes
    find "flet_tmp" -type f -exec xattr -c {} \;

    # Sign all .so and .dylib files
    find "flet_tmp" -type f -name "*.so" -exec codesign --force --verify --verbose --timestamp --options runtime --sign "$DEVELOPER_ID_APP_CERT" {} \;
    find "flet_tmp" -type f -name "*.dylib" -exec codesign --force --verify --verbose --timestamp --options runtime --sign "$DEVELOPER_ID_APP_CERT" {} \;

    # Sign all frameworks
    find "flet_tmp" -name "*.framework" -exec codesign --force --verify --verbose --timestamp --options runtime --sign "$DEVELOPER_ID_APP_CERT" {} \;

    # Sign the Flet.app bundle
    if [ -d "flet_tmp/Flet.app" ]; then
      codesign --force --verify --verbose --timestamp --options runtime --sign "$DEVELOPER_ID_APP_CERT" "flet_tmp/Flet.app"
    fi

    # Repack
    rm "$FLET_TAR_PATH"
    tar czf "$FLET_TAR_PATH" -C flet_tmp .
    rm -rf flet_tmp
  fi

  # Sign all .so and .dylib files in the flutter_assets
  echo "Signing .so and .dylib files in Flutter assets..."
  find "tmp" -type f -name "*.so"    -exec codesign --force --verify --verbose --sign "$DEVELOPER_ID_APP_CERT" --options runtime --timestamp {} \;
  find "tmp" -type f -name "*.dylib" -exec codesign --force --verify --verbose --sign "$DEVELOPER_ID_APP_CERT" --options runtime --timestamp {} \;

  echo "Repackaging and cleaning up Flutter assets..."
  cd tmp

  # Remove .venv/bin (dev tools like ruff, python executables) that can't be signed
  rm -rf .venv/bin

  # Delete old zip and create fresh one (zip -r updates existing, doesn't remove deleted files)
  rm -f ../app.zip
  zip -q -r ../app.zip .
  cd ..
  rm -rf tmp
  cd $WORKING_DIR || exit 1
}
sign_flutter_assets_package

# Sign the flet-desktop app package in serious-python
function sign_flet_desktop_package() {
  echo "Signing Flet executable and its dependent framework executables..."
  cd "$BUILD_DIR/$APP_NAME.app/Contents/Frameworks/serious_python_darwin.framework/Versions/A/Resources/python.bundle/Contents/Resources/site-packages/flet_desktop/app/" || exit 1
  mkdir -p tmp
  tar -xzf flet-macos.tar.gz -C tmp

  # Remove extended attributes that can interfere with signing
  echo "Clearing extended attributes from Flet package..."
  find "tmp" -type f -exec xattr -c {} \;

  # Sign all .so and .dylib files first (deep signing)
  echo "Signing .so and .dylib files in Flet package..."
  find "tmp" -type f -name "*.so" -exec codesign --force --verify --verbose --timestamp --options runtime --sign "$DEVELOPER_ID_APP_CERT" {} \;
  find "tmp" -type f -name "*.dylib" -exec codesign --force --verify --verbose --timestamp --options runtime --sign "$DEVELOPER_ID_APP_CERT" {} \;

  # Sign all frameworks (must sign before the app bundle)
  echo "Signing frameworks in Flet package..."
  find "tmp" -name "*.framework" -exec codesign --force --verify --verbose --timestamp --options runtime --sign "$DEVELOPER_ID_APP_CERT" {} \;

  # Sign the Flet.app bundle (signs the bundle including its executable)
  echo "Signing Flet.app bundle..."
  codesign --force --verify --verbose --timestamp --options runtime --sign "$DEVELOPER_ID_APP_CERT" "tmp/Flet.app"

  # Repack Flet and its dependencies
  echo "Repacking flet-macos.tar.gz..."
  rm flet-macos.tar.gz
  tar czf flet-macos.tar.gz -C tmp .
  rm -rf tmp
}
sign_flet_desktop_package

# Sign the local app bundle for inclusion in the .dmg
function sign_app_bundle() {
  cd "$WORKING_DIR" || exit 1

  # Remove broken symlinks and development artifacts that break code signing
  echo "Removing broken symlinks and development artifacts..."
  find "$BUILD_DIR/$APP_NAME.app" -type l ! -exec test -e {} \; -delete
  find "$BUILD_DIR/$APP_NAME.app" -type l -name ".pod" -delete

  # Remove extended attributes from all files before signing
  find "$BUILD_DIR/$APP_NAME.app" -type f -exec xattr -c {} \;

  # Sign all .so files
  find "$BUILD_DIR/$APP_NAME.app" -type f -name "*.so"    \
    -exec codesign --force --verify --verbose --sign "$DEVELOPER_ID_APP_CERT" --options runtime --timestamp {} \;
  find "$BUILD_DIR/$APP_NAME.app" -type f -name "*.dylib" \
    -exec codesign --force --verify --verbose --sign "$DEVELOPER_ID_APP_CERT" --options runtime --timestamp {} \;

  # Sign all .dylib dynamic library files - only libsodium for now
  find "libsodium" -name "*.dylib" -exec codesign --force --verify --verbose --timestamp --options runtime --sign "$DEVELOPER_ID_APP_CERT" {} \;

  # Sign the main executable
  codesign --force --verify --verbose --timestamp \
    --options runtime \
    --sign "$DEVELOPER_ID_APP_CERT" \
    --entitlements entitlements.plist \
    "$BUILD_DIR/$APP_NAME.app/Contents/MacOS/$APP_NAME"

  # Sign all frameworks
  find "$BUILD_DIR/$APP_NAME.app/Contents/Frameworks" -maxdepth 1 -name "*.framework" \
    -exec codesign --force --verify --verbose --timestamp --options runtime --sign "$DEVELOPER_ID_APP_CERT" {} \;

  # Sign the entire .app bundle
  codesign --force --verify --verbose --timestamp \
    --options runtime \
    --sign "$DEVELOPER_ID_APP_CERT" \
    --entitlements entitlements.plist \
    "$BUILD_DIR/$APP_NAME.app"

  echo "Checking for unsigned components..."
  codesign --verify --deep --verbose=4 "$BUILD_DIR/$APP_NAME.app"

#  echo "Verifying entitlements..."
#  codesign --display --entitlements entitlements.plist "$BUILD_DIR/$APP_NAME.app"
}
sign_app_bundle

# Notarize the app for independent distribution of the .dmg
function create_signed_dmg() {
  # Create the DMG
  rm -f "$BUILD_DIR/$DMG_NAME"
  hdiutil create -volname "$APP_NAME" -srcfolder "$BUILD_DIR/$APP_NAME.app" -ov -format UDZO "$BUILD_DIR/$DMG_NAME"

  # Sign the DMG
  codesign --force --verify --verbose --timestamp --options runtime --sign "$DEVELOPER_ID_APP_CERT" "$BUILD_DIR/$DMG_NAME"

  # Notarize the DMG
  xcrun notarytool submit "$BUILD_DIR/$DMG_NAME" --keychain-profile "$KC_PROFILE" --wait

  # Staple the notarization ticket to the DMG
  xcrun stapler staple "$BUILD_DIR/$DMG_NAME"

  # Verify the notarization
  xcrun stapler validate "$BUILD_DIR/$DMG_NAME"
}
create_signed_dmg

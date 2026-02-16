# Troubleshooting

## Flet Runtime Issues

### PathAccessException: Cannot create file (Operation not permitted)

**Error:**
```
PathAccessException: Cannot create file, path = '/var/folders/.../T/...' (OS Error: Operation not permitted, errno = 1)
```

**Cause:**
Flet's desktop runtime (`flet_desktop`) checks for a built app in `build/macos/` BEFORE extracting a fresh runtime. If an old build exists there (from a previous `flet build`), it will use that instead.

The production build in `build/macos/citadel.app` is signed with **sandbox entitlements** (required for notarization):
```xml
<key>com.apple.security.app-sandbox</key>
<true/>
```

This sandbox restricts temp file creation, causing the error when running in development mode.

**Solution:**
Remove or rename the `build/macos/` directory before running in development:
```bash
mv build/macos build/macos.old
# or
rm -rf build/macos
```

Then run the app again - flet will extract a fresh (non-sandboxed) runtime to `~/.flet/bin/flet-{version}/`.

**Workflow recommendation:**
After building for production, always clear `build/macos/` before resuming development:
```bash
# Build and sign for production
flet build macos
./sign.sh

# Before resuming development
rm -rf build/macos
```

**Additional checks if issue persists:**
1. Clear the flet runtime cache: `rm -rf ~/.flet/bin`
2. Clear quarantine attributes: `xattr -cr .venv/lib/python*/site-packages/flet_desktop/`
3. Verify flet version files aren't empty: `cat .venv/lib/python*/site-packages/flet_desktop/version.py`
   - If `version = ""`, upgrade flet (0.80.0 had this bug, fixed in 0.80.5+)

---

## Build Process Overview

### Building for Production (macOS)

1. **Build the app:**
   ```bash
   flet build macos
   ```
   This creates `build/macos/citadel.app`

2. **Sign and notarize:**
   ```bash
   export DEVELOPER_ID_APP_CERT="Developer ID Application: ..."
   export CITADEL_ENVIRONMENT=production  # or staging
   ./sign.sh
   ```
   This:
   - Creates Info.plist with app metadata
   - Creates entitlements.plist with sandbox permissions
   - Signs Flutter assets, flet-desktop package, and app bundle
   - Creates and notarizes the DMG

3. **Clean up for development:**
   ```bash
   rm -rf build/macos
   ```

### Required Environment Variables for Signing

- `DEVELOPER_ID_APP_CERT`: The Developer ID Application certificate name
- `CITADEL_ENVIRONMENT`: `production` or `staging` (sets LSEnvironment in Info.plist)
- Keychain profile `org.gleif.citadel` must be configured for notarization

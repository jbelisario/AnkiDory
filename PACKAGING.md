# Packaging AnkiDory for macOS

This document outlines the steps required to package AnkiDory into a standalone macOS application (.dmg).

## Prerequisites

- Python 3.8+ (matching your development environment)
- PyInstaller (`pip install pyinstaller`)
- create-dmg (`brew install create-dmg`)

## Steps for Packaging

### 1. Environment Preparation

1. Create a fresh virtual environment for building:
```bash
python -m venv build_env
source build_env/bin/activate
pip install -r requirements.txt
pip install pyinstaller
```

### 2. Application Bundling with PyInstaller

1. Create a PyInstaller spec file (`AnkiDory.spec`):
```python
block_cipher = None

a = Analysis(['tools/run.py'],
    pathex=['/Users/cornucopian/CascadeProjects/AnkiDory'],
    binaries=[],
    datas=[
        ('src/ankidory', 'ankidory'),
        # Add any additional data files/directories needed
    ],
    hiddenimports=[
        'openai',
        'groq',
        'fitz',  # PyMuPDF
        'httpx',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AnkiDory',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='path/to/icon.icns'  # You'll need to create an icon
)

coll = COLLECT(exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AnkiDory'
)

app = BUNDLE(coll,
    name='AnkiDory.app',
    icon='path/to/icon.icns',
    bundle_identifier='com.ankidory.app',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.12.0',
    },
)
```

2. Build the application:
```bash
pyinstaller AnkiDory.spec
```

### 3. Creating the DMG

1. Create a DMG file:
```bash
create-dmg \
  --volname "AnkiDory" \
  --volicon "path/to/icon.icns" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "AnkiDory.app" 175 120 \
  --hide-extension "AnkiDory.app" \
  --app-drop-link 425 120 \
  "AnkiDory.dmg" \
  "dist/AnkiDory.app"
```

## Important Considerations

1. **Environment Variables**: 
   - Ensure all necessary environment variables are properly set in the packaged application
   - API keys and configurations should be handled appropriately

2. **File Paths**:
   - Update all hardcoded paths to use relative paths or appropriate application bundle paths
   - Use `sys._MEIPASS` for accessing bundled resources when running as a frozen application

3. **Dependencies**:
   - All required Python packages must be included in the PyInstaller spec
   - Binary dependencies (if any) must be properly bundled
   - Qt resources must be properly included

4. **Testing**:
   - Test the packaged application on a clean macOS system
   - Verify all functionality works as expected
   - Check for any missing dependencies or resources

## Distribution

1. **Code Signing**:
   - For distribution outside of development, the application should be code signed with an Apple Developer certificate
   - Consider notarization for better security and user experience

2. **Updates**:
   - Consider implementing an update mechanism
   - Document the update process for users

## Troubleshooting

Common issues and their solutions:

1. **Missing Resources**: 
   - Check the `datas` section in the spec file
   - Use PyInstaller's `--debug` option to trace resource loading

2. **Dynamic Libraries**:
   - Use `otool -L` to check library dependencies
   - Ensure all required libraries are bundled

3. **Permissions**:
   - Set appropriate permissions for the application bundle
   - Handle file access permissions properly

## Notes

- The packaged application will maintain the same functionality as running through the Python interpreter
- Users won't need to install Python or any dependencies
- The application will be self-contained in the .app bundle

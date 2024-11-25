# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Get all hidden imports
hidden_imports = [
    'anki',
    'anki.storage',
    'anki.rsbackend',
    'anki.collection',
    'anki.utils',
    'anki.hooks',
    'anki.cards',
    'anki.decks',
    'anki.models',
    'anki.scheduler',
    'groq',
    'openai',
    'httpx',
    'markdown',
    'jsonschema',
    'certifi',
    'orjson',
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'PyQt6.QtGui',
    'PyQt6.QtWebEngineCore',
    'PyQt6.QtWebEngineWidgets',
    'PyQt6.QtNetwork',
    'PyQt6.QtPrintSupport',
    'PyQt6.QtWebChannel',
    'PyQt6.QtMultimedia',
]

# Get the project root directory
project_root = os.path.abspath(os.getcwd())

# Add source files
src_path = os.path.join(project_root, 'src', 'ankidory')
src_files = []
for root, dirs, files in os.walk(src_path):
    for file in files:
        if file.endswith('.py'):
            src_files.append((os.path.join(root, file), os.path.relpath(root, src_path)))

# Collect all data files
datas = []
datas.extend(src_files)
datas.extend(collect_data_files('anki'))
datas.extend(collect_data_files('groq'))
datas.extend(collect_data_files('openai'))
datas.extend(collect_data_files('markdown'))
datas.extend(collect_data_files('jsonschema'))
datas.extend(collect_data_files('certifi'))

# Add project files
datas.extend([
    (os.path.join(project_root, 'src', 'ankidory', 'config.ini'), 'ankidory'),
    (os.path.join(project_root, 'src', 'ankidory', 'resources'), 'ankidory/resources'),
])

# Add PyQt6 plugins
qt_plugins = []
for plugin in ['platforms', 'styles', 'imageformats', 'sqldrivers', 'multimedia']:
    plugin_dir = os.path.join('PyQt6', 'Qt6', 'plugins', plugin)
    qt_plugins.extend(collect_data_files('PyQt6', include_py_files=True, subdir=plugin_dir))
datas.extend(qt_plugins)

# Add PyQt6 translations and resources
qt_translations = collect_data_files('PyQt6', include_py_files=True, subdir=os.path.join('Qt6', 'translations'))
datas.extend(qt_translations)

qt_resources = collect_data_files('PyQt6', include_py_files=True, subdir=os.path.join('Qt6', 'resources'))
datas.extend(qt_resources)

# Add anki media
anki_media = os.path.join(os.path.expanduser('~'), '.local', 'share', 'Anki2')
if os.path.exists(anki_media):
    datas.extend([(anki_media, 'Anki2')])

a = Analysis(
    [os.path.join(project_root, 'src', 'ankidory', 'main.py')],
    pathex=[project_root, src_path],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AnkiDory',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to True temporarily for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AnkiDory',
)

app = BUNDLE(
    coll,
    name='AnkiDory.app',
    icon=None,
    bundle_identifier='com.ankidory.app',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
        'NSRequiresAquaSystemAppearance': False,
    },
)

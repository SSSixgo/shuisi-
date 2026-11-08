# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_match.py'],  # ★ 这里必须是你的入口文件
    pathex=[],
    binaries=[],
    datas=[('app1.ico', '.')],  # ★ 把图标一起打进去
    hiddenimports=['customtkinter', 'pymupdf', 'rapidfuzz', 'pandas', 'PIL', 'fitz'],
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
    name='水司智搜',  # 生成的 exe 名字
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                 # ★ 防误杀关键：禁用 UPX
    console=False,             # 隐藏黑框
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app1.ico',
    version='version_info.txt' # ★ 如果你有版本信息文件，保留这个；如果没有，把它删掉
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,                 # ★ 防误杀关键：禁用 UPX
    upx_exclude=[],
    name='水司智搜'
)
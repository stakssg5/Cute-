# PyInstaller spec file for Crypto PR+ Desktop
# Build with: pyinstaller build.spec

block_cipher = None

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = [] + collect_submodules('tkinter')

a = Analysis(['app/main.py'],
             pathex=['.'],
             binaries=[],
             datas=[],
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Jonathanzoes',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Jonathanzoes')

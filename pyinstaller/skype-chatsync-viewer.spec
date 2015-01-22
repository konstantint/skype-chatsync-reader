# -*- mode: python -*-
import os
a = Analysis(['skype-chatsync-viewer.py'],
             pathex=[os.path.abspath('.')],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='skype-chatsync-viewer.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='Umut-Pulat-Tulliana-2-Log.ico')

"""bpy (Python モジュール版 Blender) でスクリプトを動かす小さな入口。

    BLENDER_USER_RESOURCES=/dev/shm/sena/userres PYTHONPATH=/dev/shm/bpy \
        python3.11 run.py build_sena.py -- --quick

ログはファイルへ流すこと (パイプにつなぐと終了時に止まることがある)。
"""
import os
import runpy
import sys

script = os.path.abspath(sys.argv[1])
sys.argv = [script] + sys.argv[2:]
import traceback
try:
    runpy.run_path(script, run_name="__main__")
except BaseException:
    traceback.print_exc()
finally:
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)

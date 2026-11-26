#!/bin/bash
# (クラウドで使っていた写し。2026-11-26 にリポジトリへ。ローカルで使うときは docs/society_phase/local_gpu_prompt.md のとおり、/dev/shm と /root とリポジトリの場所を自分の PC のフォルダに読みかえる)
# 再起動のあとの準備 (/dev/shm は再起動で消える): bpy・VRoid のサンプル・CMU の動き。スワップも
set -e
swapon /swapfile 2>/dev/null || true
mkdir -p /dev/shm/tmp /dev/shm/heads/src /dev/shm/cmu /dev/shm/sena/vroid/logs
if [ ! -f /dev/shm/cmu/una/data/026/26_10.bvh ]; then rm -rf /dev/shm/cmu/una; cd /dev/shm/cmu && git clone -q --filter=blob:none --no-checkout https://github.com/una-dinosauria/cmu-mocap una && cd una && git checkout -q 09a07f54f3bbb58797325f009282d0b2048a2871 -- data/008/08_01.bvh data/013/13_10.bvh data/015/15_07.bvh data/018/18_08.bvh data/022/22_13.bvh data/069/69_73.bvh data/077/77_06.bvh data/077/77_08.bvh data/077/77_16.bvh data/077/77_25.bvh data/079/79_12.bvh data/062/62_07.bvh data/062/62_21.bvh data/026/26_10.bvh; fi
if [ ! -f /dev/shm/heads/src/vrmsamples/vroid/beta/Victoria_Rubin.vrm ]; then rm -rf /dev/shm/heads/src/vrmsamples; cd /dev/shm/heads/src && git clone -q --filter=blob:none --no-checkout https://github.com/madjin/vrm-samples vrmsamples && cd vrmsamples && git checkout -q HEAD -- vroid/beta/Sendagaya_Shino.vrm vroid/beta/HairSample_Female.vrm vroid/beta/HairSample_Male.vrm vroid/beta/Sakurada_Fumiriya.vrm vroid/beta/Victoria_Rubin.vrm; fi
[ -d /dev/shm/bpy/bpy ] || TMPDIR=/dev/shm/tmp python3.11 -m pip install -q --no-cache-dir --target /dev/shm/bpy "bpy==4.5.*" 2>&1 | grep -v WARNING || true
[ -d /dev/shm/bpy/bpy ] && echo "env ok"
# 前に作った人のモデル (服なし: 前の動画用) を戻す
[ -f /root/people_glb/sena.glb ] && mkdir -p /dev/shm/people_glb && cp -n /root/people_glb/* /dev/shm/people_glb/
for e in hide leather; do [ -f /root/people_glb_$e/sena.glb ] && mkdir -p /dev/shm/people_glb_$e && cp -n /root/people_glb_$e/* /dev/shm/people_glb_$e/; done
true

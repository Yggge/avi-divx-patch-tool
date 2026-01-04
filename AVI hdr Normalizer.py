#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AVI header normalizer for compressed DIVX (no re-encode)

- Fixes display width/height
- Sets biSizeImage = 0
- Sets lSampleSize = 0
- Keeps FOURCC and bitstream intact
- Makes .bak backup
"""

import os
import shutil
import struct

# ===== НАСТРОЙКИ =====
WIDTH  = 512
HEIGHT = 384
# =====================

def normalize_avi(path):
    bak = path + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)

    try:
        with open(path, "r+b") as f:
            # biPlanes = 1
            f.seek(0xB1)
            f.write(struct.pack("<H", 1))

            # biWidth (display)
            f.seek(0xB4)
            f.write(struct.pack("<i", WIDTH))

            # biHeight (display)
            f.seek(0xB8)
            f.write(struct.pack("<i", HEIGHT))

            # biSizeImage = 0 (compressed video!)
            f.seek(0xC0)
            f.write(struct.pack("<I", 0))

            # lSampleSize = 0 (compressed)
            f.seek(0x9C)
            f.write(struct.pack("<I", 0))

        print(f"[OK] {os.path.basename(path)}")
        return True

    except Exception as e:
        print(f"[ERR] {os.path.basename(path)}: {e}")
        return False


if __name__ == "__main__":
    print("AVI format normalizer (DIVX, no re-encode)")
    print(f"Display size: {WIDTH}x{HEIGHT}")
    print(f"Folder: {os.getcwd()}\n")

    ok = err = 0

    for root, _, files in os.walk(os.getcwd()):
        for name in files:
            if name.lower().endswith(".avi"):
                full = os.path.join(root, name)
                if normalize_avi(full):
                    ok += 1
                else:
                    err += 1

    print(f"\nNormalized: {ok}, Errors: {err}")

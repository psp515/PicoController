"""
Build helper (runs on normal CPython, not MicroPython): cross-compiles all
device .py sources to .mpy bytecode with mpy-cross and assembles a ready-to-
copy device image in helpers/release/, mirroring the on-device layout
(main.py stays as source so MicroPython auto-runs it; everything under src/
and lib/ becomes .mpy; Web UI static assets are copied as-is).

Requires the mpy-cross pip package: python -m pip install mpy-cross
The mpy-cross version must match the device's MicroPython firmware
(.mpy bytecode format is version-locked).

Usage:
    python helpers/build_release.py
"""
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RELEASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "release")
SOURCE_DIRS = ["src", "lib"]
KEEP_AS_SOURCE = ["main.py"]
SKIP_DIRS = {"__pycache__"}
STATIC_DIR = os.path.join("src", "webui", "static")


def compile_to_mpy(source, dest):
    result = subprocess.run(
        [sys.executable, "-m", "mpy_cross", source, "-o", dest],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("mpy-cross failed for", source)
        print(result.stderr.strip())
        sys.exit(1)


def build():
    if os.path.exists(RELEASE_DIR):
        shutil.rmtree(RELEASE_DIR)
    os.makedirs(RELEASE_DIR)

    compiled = 0
    copied = 0

    for name in KEEP_AS_SOURCE:
        shutil.copy2(os.path.join(REPO_ROOT, name), os.path.join(RELEASE_DIR, name))
        copied += 1

    for source_dir in SOURCE_DIRS:
        for dirpath, dirnames, filenames in os.walk(os.path.join(REPO_ROOT, source_dir)):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            relative_dir = os.path.relpath(dirpath, REPO_ROOT)
            out_dir = os.path.join(RELEASE_DIR, relative_dir)
            for filename in filenames:
                source = os.path.join(dirpath, filename)
                if filename.endswith(".py"):
                    os.makedirs(out_dir, exist_ok=True)
                    dest = os.path.join(out_dir, filename[:-3] + ".mpy")
                    compile_to_mpy(source, dest)
                    compiled += 1
                elif relative_dir.startswith(STATIC_DIR):
                    os.makedirs(out_dir, exist_ok=True)
                    shutil.copy2(source, os.path.join(out_dir, filename))
                    copied += 1

    print(f"release built in {RELEASE_DIR}")
    print(f"compiled {compiled} .py -> .mpy, copied {copied} files")


if __name__ == "__main__":
    build()

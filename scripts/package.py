#!/usr/bin/env python3
"""Build a native MindMap artifact for the current operating system."""

import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def run(*args):
    subprocess.check_call([str(value) for value in args], cwd=str(ROOT))


def main():
    run(sys.executable, ROOT / "scripts" / "build_icons.py")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    # Build outside the checkout. Cloud storage can re-attach Finder metadata
    # to .app contents between signing and DMG creation.
    with tempfile.TemporaryDirectory(prefix="mindmap-build-") as staging_dir:
        staging = Path(staging_dir)
        dist = staging / "dist"
        work = staging / "build"
        run(
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
            "--distpath", dist, "--workpath", work, ROOT / "MindMap.spec",
        )

        system = platform.system()
        architecture = platform.machine().lower().replace("amd64", "x86_64")
        if system == "Darwin":
            app = dist / "MindMap.app"
            output = ARTIFACTS / "MindMap-macOS-{}.dmg".format(architecture)
            if output.exists():
                output.unlink()
            run("xattr", "-cr", app)
            run("codesign", "--force", "--deep", "--sign", "-", app)
            run("codesign", "--verify", "--deep", "--strict", app)
            run(
                "hdiutil", "create", "-volname", "MindMap",
                "-srcfolder", app, "-ov", "-format", "UDZO", output,
            )
        elif system == "Windows":
            source = dist / "MindMap.exe"
            output = ARTIFACTS / "MindMap-Windows-{}.exe".format(architecture)
            shutil.copy2(str(source), str(output))
        else:
            raise SystemExit("Packaging is configured for Windows and macOS only.")

    print("Built {}".format(output))


if __name__ == "__main__":
    main()

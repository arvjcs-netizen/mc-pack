"""Build a resource pack zip, and optionally install or link it into Minecraft.

Usage:
    python build.py                       # MyPack: creates dist/MyPack.zip
    python build.py --pack tidal          # Tidal:  creates dist/Tidal.zip
    python build.py --install             # also copies the zip into .minecraft/resourcepacks
    python build.py --pack tidal --link   # link the folder into resourcepacks for live editing (F3+T)
"""
import argparse
import os
import platform
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
DIST_DIR = ROOT / "dist"
PACKS = {  # --pack name: (source folder, output / in-game name)
    "mypack": (ROOT / "pack", "MyPack"),
    "tidal": (ROOT / "packs" / "tidal", "Tidal"),
    "gradient": (ROOT / "packs" / "mypack_gradient", "MyPack Gradient"),
}
SKIP = {".gitkeep", ".DS_Store", "Thumbs.db"}


def minecraft_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        return Path(os.environ["APPDATA"]) / ".minecraft"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "minecraft"
    return Path.home() / ".minecraft"


def build(src: Path, name: str) -> Path:
    DIST_DIR.mkdir(exist_ok=True)
    out = DIST_DIR / f"{name}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src.rglob("*")):
            if path.is_file() and path.name not in SKIP:
                # pack.mcmeta must sit at the zip root, so paths are relative to the pack folder
                zf.write(path, path.relative_to(src).as_posix())
    print(f"Built {out}")
    return out


def install(zip_path: Path) -> None:
    target = minecraft_dir() / "resourcepacks"
    if not target.exists():
        print(f"Couldn't find {target}; copy the zip there manually.")
        return
    shutil.copy2(zip_path, target / zip_path.name)
    print(f"Installed to {target / zip_path.name}  (press F3+T in-game to reload)")


def link(src: Path, name: str) -> None:
    """Link .minecraft/resourcepacks/<name> to the pack folder so edits show up on F3+T, no restart."""
    target = minecraft_dir() / "resourcepacks"
    if not target.exists():
        print(f"Couldn't find {target}.")
        return
    dest = target / name
    if dest.exists() or dest.is_symlink():
        print(f"{dest} already exists; leaving it alone.")
        return
    if platform.system() == "Windows":
        # A directory junction needs no admin rights, unlike a symlink.
        subprocess.run(["cmd", "/c", "mklink", "/J", str(dest), str(src.resolve())], check=True)
    else:
        os.symlink(src.resolve(), dest, target_is_directory=True)
    print(f"Linked {dest} -> {src.resolve()}  (enable '{name}' in-game, then F3+T after edits)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", choices=sorted(PACKS), default="mypack")
    parser.add_argument("--install", action="store_true", help="copy the zip into resourcepacks")
    parser.add_argument("--link", action="store_true", help="link the pack folder into resourcepacks for live editing")
    args = parser.parse_args()
    src, name = PACKS[args.pack]
    if args.link:
        link(src, name)
    else:
        z = build(src, name)
        if args.install:
            install(z)

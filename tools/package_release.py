"""Đóng gói bản phát hành chạy được cho GitHub Release (Phase 4, AC-P4-05).

Chạy:
  python3 tools/package_release.py --version v1.0.0

Tạo `dist/cho-noi-<version>.tar.gz` và `dist/cho-noi-<version>.zip` gồm toàn bộ mã chạy game,
`game.contract.json`, `README.md`, `CHANGELOG.md`, `CREDITS.md`, `LICENSE`. Không kèm `.git`, `__pycache__`, `dist/`.
"""

import argparse
import os
import tarfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCLUDE_FILES = ("game.contract.json", "README.md", "CHANGELOG.md", "CREDITS.md", "LICENSE")
INCLUDE_DIRS = ("chonoi",)
SKIP_PARTS = {"__pycache__", ".git", ".DS_Store"}


def _iter_files():
    for rel in INCLUDE_FILES:
        full = os.path.join(ROOT, rel)
        if os.path.isfile(full):
            yield rel, full
    for d in INCLUDE_DIRS:
        base = os.path.join(ROOT, d)
        for cur, dirs, files in os.walk(base):
            dirs[:] = sorted(x for x in dirs if x not in SKIP_PARTS)
            for name in sorted(files):
                if name.endswith(".pyc") or name in SKIP_PARTS:
                    continue
                full = os.path.join(cur, name)
                rel = os.path.relpath(full, ROOT).replace("\\", "/")
                yield rel, full


def build_archives(version: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    prefix = f"cho-noi-{version}"
    files = list(_iter_files())
    tar_path = os.path.join(out_dir, f"{prefix}.tar.gz")
    zip_path = os.path.join(out_dir, f"{prefix}.zip")

    with tarfile.open(tar_path, "w:gz") as tf:
        for rel, full in files:
            tf.add(full, arcname=f"{prefix}/{rel}")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel, full in files:
            zf.write(full, arcname=f"{prefix}/{rel}")

    return tar_path, zip_path, len(files)


def main():
    p = argparse.ArgumentParser(description="Đóng gói bản phát hành Quán Ăn Chợ Nổi")
    p.add_argument("--version", default="v1.0.0", help="Nhãn phiên bản (mặc định v1.0.0)")
    p.add_argument("--out-dir", default=os.path.join(ROOT, "dist"), help="Thư mục xuất gói")
    a = p.parse_args()
    tar_path, zip_path, count = build_archives(a.version, a.out_dir)
    print(f"Đã đóng gói {count} file:")
    print(f"  - {tar_path}")
    print(f"  - {zip_path}")


if __name__ == "__main__":
    main()

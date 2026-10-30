"""Package release archive deterministically for SAT-Frontier v0.2.7."""
import hashlib
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE_DIR = ROOT / "artifacts" / "release"
RELEASE_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_PATH = RELEASE_DIR / "sat-frontier-v0.2.7.zip"

EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    "build",
    "dist",
    "sat_frontier.egg-info",
    ".pytest_cache",
    ".mypy_cache",
}

EXCLUDE_EXTS = {
    ".pyc",
    ".pyo",
}

def should_exclude(rel_path: Path) -> bool:
    parts = rel_path.parts
    for p in parts:
        if p in EXCLUDE_DIRS:
            return True
    if rel_path.suffix in EXCLUDE_EXTS:
        return True
    if len(parts) >= 2 and parts[0] == "artifacts" and parts[1] == "release":
        if rel_path.suffix == ".zip":
            return True
    return False

def main():
    if ARCHIVE_PATH.exists():
        ARCHIVE_PATH.unlink()

    files_to_pack = []
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            full_path = Path(root) / f
            rel_path = full_path.relative_to(ROOT)
            if not should_exclude(rel_path):
                files_to_pack.append(rel_path)

    files_to_pack.sort()
    prefix = "sat-frontier-v0.2.7"

    print(f"Packaging {len(files_to_pack)} files into {ARCHIVE_PATH.name}...")
    with zipfile.ZipFile(ARCHIVE_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in files_to_pack:
            archive_name = f"{prefix}/{rel.as_posix()}"
            zf.write(ROOT / rel, archive_name)

    data = ARCHIVE_PATH.read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    size = len(data)

    print(f"Archive built successfully:")
    print(f"  Name:   {ARCHIVE_PATH.name}")
    print(f"  Size:   {size:,} bytes")
    print(f"  Files:  {len(files_to_pack):,}")
    print(f"  SHA256: {sha256}")

    return sha256, size, len(files_to_pack)

if __name__ == "__main__":
    main()


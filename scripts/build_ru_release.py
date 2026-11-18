"""Build the RU portable release from a reviewed, hash-pinned file allowlist."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {"settings.xml", "poe_api_response.json", "installed.cfg", "first.run", "imgui.ini"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_name(name: str) -> None:
    parts = Path(name).parts
    if Path(name).is_absolute() or ".." in parts or any(p.lower() in {"builds", ".git", "__pycache__"} for p in parts):
        raise ValueError(f"Disallowed package path: {name}")
    if Path(name).name.lower() in FORBIDDEN:
        raise ValueError(f"User data cannot be packaged: {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--refresh-manifest", action="store_true", help="Explicitly accept reviewed source changes before rebuilding")
    args = parser.parse_args()
    config_path = ROOT / "localization/release.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    manifest_path = ROOT / "localization/portable-files.json"
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    output = args.output.resolve()
    folder_name = config["archiveRoot"]
    target = output / folder_name
    archive = output / config["archiveName"]
    if target.exists() or archive.exists():
        raise FileExistsError("Use a new output directory; an existing build is never overwritten")
    for entry in entries:
        validate_name(entry["path"])
        source = (ROOT / entry["source"]).resolve()
        if not source.is_relative_to(ROOT) or ".git" in source.parts:
            raise ValueError("Source must be inside the checked-out repository")
        actual = digest(source)
        if args.refresh_manifest:
            entry["sha256"] = actual
        elif actual != entry["sha256"]:
            raise ValueError(f"Source changed; review before --refresh-manifest: {entry['source']}")
    if args.refresh_manifest:
        manifest_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    target.mkdir(parents=True)
    for entry in entries:
        destination = target / entry["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / entry["source"], destination)
    output.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive, "w", ZIP_DEFLATED, compresslevel=6) as zipped:
        for entry in sorted(entries, key=lambda e: e["path"]):
            name = folder_name + "/" + entry["path"]
            info = ZipInfo(name, (2026, 11, 18, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zipped.writestr(info, (target / entry["path"]).read_bytes())
    with ZipFile(archive) as zipped:
        expected = {folder_name + "/" + e["path"]: e for e in entries}
        assert set(zipped.namelist()) == set(expected)
        assert zipped.testzip() is None
        for name, entry in expected.items():
            assert hashlib.sha256(zipped.read(name)).hexdigest() == entry["sha256"], name
    checksum = output / "SHA256SUMS.txt"
    checksum.write_text(digest(archive) + "  " + archive.name + "\n", encoding="ascii")
    print(f"Built {archive.name}: {archive.stat().st_size} bytes, {len(entries)} reviewed files")
    print(f"SHA256 {digest(archive)}")


if __name__ == "__main__":
    main()

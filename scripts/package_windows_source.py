"""Build a source-only Windows ZIP for the YouTube-disabled initial release."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import ast
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_NAME = "PuyoAnalysis-Source-Windows-v1.0.1.zip"
OUT = ROOT / "dist" / ARCHIVE_NAME
FILES = [
    "README.md", "GUIDE.md", "LICENSE", "THIRD_PARTY_NOTICES.md",
    "SETUP_FIRST.bat", "START_Analysis.bat",
    "requirements-windows.txt",
    "puyo_tools/app.py", "puyo_tools/record_store.py", "puyo_tools/crop_suggest.py", "puyo_tools/tenpai_probe.py",
    "puyo_tools/common/__init__.py", "puyo_tools/common/analysis.py",
    "puyo_tools/common/engine.py", "puyo_tools/common/image_board.py",
    "puyo_tools/common/reference.py", "puyo_tools/common/time_calc.py",
    "puyo_tools/assets/small.png", "puyo_tools/assets/large.png",
    "puyo_tools/assets/red.png", "puyo_tools/assets/star.png",
    "puyo_tools/assets/moon.png", "puyo_tools/assets/crown.png",
]
BANNED = ("youtube_player.py", "youtube_capture.py", "youtube_dock.py", "webview_host.py")
SENSITIVE = (
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    r"(?i)[a-z0-9._%+-]+@(?!users\\.noreply\\.github\\.com)[a-z0-9.-]+\\.[a-z]{2,}",
    r"(?i)[a-z]:\\\\Users\\\\[^\\\\]+\\\\",
)

def main():
    OUT.parent.mkdir(exist_ok=True)
    for name in FILES:
        p = ROOT / name
        if not p.is_file():
            raise RuntimeError(f"Missing: {name}")
        if p.suffix == ".py":
            ast.parse(p.read_text(encoding="utf-8-sig"), filename=name)
        if p.suffix.lower() in (".py", ".md", ".txt", ".bat"):
            content = p.read_text(encoding="utf-8-sig")
            for pattern in SENSITIVE:
                if re.search(pattern, content):
                    raise RuntimeError(f"Review potential secret in {name}")
    if any("youtube" in name.lower() or name in ("review.py", "START_Review.bat") for name in FILES):
        raise RuntimeError("Analysis-only ZIP includes review/YouTube entry point")
    with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
        for name in FILES:
            z.write(ROOT / name, f"PuyoAnalysis-Source-Windows-v1.0.1/{name}")
    with ZipFile(OUT) as z:
        assert z.testzip() is None
        names = z.namelist()
        assert len(names) == len(FILES)
        assert not any(any(b in n for b in BANNED) for n in names)
    print(f"Created {OUT} ({OUT.stat().st_size} bytes)")
    print(f"SHA256: {hashlib.sha256(OUT.read_bytes()).hexdigest()}")
if __name__ == "__main__":
    main()

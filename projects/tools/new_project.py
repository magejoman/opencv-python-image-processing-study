"""_template 을 복사해 새 프로젝트 폴더를 만든다.

    python tools/new_project.py p1_doc_scanner "문서 스캐너"
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # projects/
TEMPLATE = ROOT / "_template"
TEXT_FILES = ("README.md", "main.py", "config.yaml", "tests/test_pipeline.py")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    name = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else name
    if not re.fullmatch(r"[a-z0-9_]+", name):
        sys.exit(f"폴더 이름은 영문 소문자·숫자·밑줄만 씁니다 (예: p1_doc_scanner): {name!r}")
    dest = ROOT / name
    if dest.exists():
        sys.exit(f"이미 있습니다: {dest}")

    shutil.copytree(TEMPLATE, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for results_item in (dest / "results").iterdir():     # 템플릿을 시험 실행한 결과물은 가져오지 않는다
        if results_item.name != ".gitkeep":
            shutil.rmtree(results_item) if results_item.is_dir() else results_item.unlink()
    for fname in TEXT_FILES:
        f = dest / fname
        f.write_text(f.read_text(encoding="utf-8").replace("{{TITLE}}", title).replace("{{NAME}}", name),
                     encoding="utf-8")

    print(f"만들었습니다: {dest}")
    print(f"  1) {dest / 'data' / 'raw'} 에 사진을 넣고")
    print(f"  2) python {name}/main.py  로 실행해 보세요 (결과는 {name}/results/)")


if __name__ == "__main__":
    main()

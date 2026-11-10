"""pytest 없이 테스트를 돌린다.

    python tools/run_tests.py              # projects/tests/ 와 각 프로젝트의 tests/ 전부
    python tools/run_tests.py p1_doc_scanner   # 특정 프로젝트만 (+ cvkit 테스트)

규칙: tests/test_*.py 파일 안의 test_* 함수를 인자 없이 호출한다. assert 가 실패하면 FAIL.
"""
from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # projects/


def find_test_files(only: str | None):
    files = sorted((ROOT / "tests").glob("test_*.py"))
    for proj in sorted(p for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))):
        if only and proj.name != only:
            continue
        files += sorted((proj / "tests").glob("test_*.py"))
    return files


def run_file(path: Path):
    proj_dir = path.parent.parent
    sys.path.insert(0, str(proj_dir))               # 프로젝트 폴더의 모듈(main.py 등)을 import 할 수 있게
    spec = importlib.util.spec_from_file_location(f"_t_{proj_dir.name}_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
        # 프로젝트마다 main.py 가 있으므로, 다음 프로젝트가 이전 프로젝트의 main 을 재사용하지 않게 지운다
        for name, mod in list(sys.modules.items()):
            f = getattr(mod, "__file__", None)
            if f and name != "__main__" and Path(f).resolve().is_relative_to(proj_dir) and proj_dir != ROOT:
                del sys.modules[name]
    results = []
    for name in sorted(n for n in vars(module) if n.startswith("test_") and callable(getattr(module, n))):
        try:
            getattr(module, name)()
            results.append((name, None))
        except Exception:
            results.append((name, traceback.format_exc()))
    return results


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    passed = failed = 0
    for path in find_test_files(only):
        print(f"\n== {path.relative_to(ROOT)}")
        for name, err in run_file(path):
            if err is None:
                passed += 1
                print(f"  PASS  {name}")
            else:
                failed += 1
                print(f"  FAIL  {name}\n" + "\n".join("        " + line for line in err.rstrip().splitlines()))
    print(f"\n결과: {passed} 통과, {failed} 실패")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

"""(제공) 직접 찍은 사진에 정답 꼭짓점 찍기 → 이미지 폴더의 gt.json

    python p1_doc_scanner/tools/label_corners.py                 # data/raw 에서 정답 없는 사진만
    python p1_doc_scanner/tools/label_corners.py --redo          # 이미 찍은 것도 다시 (기존 점이 미리 찍혀 나옴)
    python p1_doc_scanner/tools/label_corners.py --folder data/raw

조작: 좌클릭 좌상→우상→우하→좌하 | 우클릭 되돌리기 | Enter 확정 | s 건너뛰기 | ESC 종료
한 장 확정할 때마다 바로 저장하므로 중간에 꺼도 된다.

※ 라벨링도 현업의 중요한 일이다. 꼭짓점을 '정확히' 찍는 게 생각보다 어렵다는 것,
  그리고 사람이 찍은 정답에도 몇 px 오차가 있다는 것을 체감해 보자.
"""
import argparse
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from cvkit import imread, list_images  # noqa: E402
from scanner.evaluate import load_gt, save_gt  # noqa: E402
from scanner.ui import pick_corners  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", default="data/raw")
    ap.add_argument("--redo", action="store_true")
    args = ap.parse_args()

    folder = PROJECT / args.folder
    gt = load_gt(folder)
    todo = [p for p in list_images(folder) if args.redo or p.name not in gt]
    print(f"{folder}: 전체 {len(list_images(folder))}장, 이번에 라벨링할 사진 {len(todo)}장")

    for i, path in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {path.name}")
        result = pick_corners(imread(path), initial=gt.get(path.name), window="label")
        if isinstance(result, str):          # "quit"
            break
        if result is not None:
            gt[path.name] = result
            save_gt(folder, gt)
    print(f"저장: {folder / 'gt.json'} ({len(gt)}장)")


if __name__ == "__main__":
    main()

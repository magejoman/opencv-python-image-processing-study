"""결과표. 이미지마다 지표를 한 줄씩 쌓고, 마크다운(README 붙여넣기용)이나 CSV(엑셀용)로 저장한다.

    table = Table()
    table.add(file="001.jpg", success=True, corner_err_px=2.3)
    table.add(file="002.jpg", success=False, reason="그림자")
    print(table)                               # 마크다운 표
    table.save_csv(proj.result_path("summary.csv"))
"""
from __future__ import annotations

import csv
from pathlib import Path


def _fmt(v, floatfmt: str) -> str:
    if isinstance(v, bool):
        return "O" if v else "X"
    if isinstance(v, float):
        return format(v, floatfmt)
    return "" if v is None else str(v)


class Table:
    def __init__(self):
        self.rows: list[dict] = []

    def add(self, **row) -> None:
        self.rows.append(row)

    @property
    def columns(self) -> list[str]:
        cols: list[str] = []
        for row in self.rows:
            cols += [k for k in row if k not in cols]
        return cols

    def column(self, name: str) -> list:
        return [row.get(name) for row in self.rows]

    def mean(self, name: str) -> float:
        """숫자 열의 평균 (빈 칸은 건너뛴다). bool 열이면 비율(성공률)이 된다."""
        vals = [float(v) for v in self.column(name) if v is not None]
        return sum(vals) / len(vals) if vals else float("nan")

    def __len__(self):
        return len(self.rows)

    def to_markdown(self, floatfmt: str = ".3f") -> str:
        cols = self.columns
        if not cols:
            return "(빈 표)"
        lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        for row in self.rows:
            lines.append("| " + " | ".join(_fmt(row.get(c), floatfmt) for c in cols) + " |")
        return "\n".join(lines)

    __str__ = to_markdown

    def save_markdown(self, path, floatfmt: str = ".3f") -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_markdown(floatfmt) + "\n", encoding="utf-8")
        return path

    def save_csv(self, path) -> Path:
        """utf-8-sig 로 저장해서 엑셀에서 열어도 한글이 깨지지 않게 한다."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writeheader()
            writer.writerows(self.rows)
        return path

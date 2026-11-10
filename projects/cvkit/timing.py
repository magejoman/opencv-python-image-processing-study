"""처리 시간 측정.

    with Timer("canny"):                 # 한 번 재기
        edges = cv2.Canny(gray, 50, 150)

    r1 = benchmark(my_warp, img, H, name="직접 구현")           # 여러 번 돌려 중앙값
    r2 = benchmark(cv2.warpPerspective, img, H, (w, h), name="OpenCV")
    print(speed_table(r1, r2))
"""
from __future__ import annotations

import statistics
import time
from dataclasses import dataclass


class Timer:
    """with 블록의 실행 시간을 ms 로 잰다. 끝나면 .ms 에 남는다."""

    def __init__(self, name: str = "", *, verbose: bool = True):
        self.name = name
        self.verbose = verbose
        self.ms = 0.0

    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.ms = (time.perf_counter() - self._t0) * 1000
        if self.verbose:
            print(f"[시간] {self.name or '블록'}: {self.ms:.2f} ms")
        return False


@dataclass
class BenchResult:
    name: str
    median_ms: float
    min_ms: float
    mean_ms: float
    repeat: int

    def __str__(self) -> str:
        return (f"[벤치] {self.name}: 중앙값 {self.median_ms:.3f} ms "
                f"(최소 {self.min_ms:.3f}, 평균 {self.mean_ms:.3f}, {self.repeat}회)")


def benchmark(fn, *args, repeat: int = 20, warmup: int = 3, name: str | None = None,
              verbose: bool = True, **kwargs) -> BenchResult:
    """fn(*args, **kwargs) 를 여러 번 실행해 시간을 잰다.

    처음 몇 번(warmup)은 캐시·메모리 할당 영향이 커서 버린다.
    평균보다 중앙값을 대표값으로 쓴다 (가끔 튀는 값에 덜 흔들린다).
    """
    for _ in range(warmup):
        fn(*args, **kwargs)
    times = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn(*args, **kwargs)
        times.append((time.perf_counter() - t0) * 1000)
    result = BenchResult(name or getattr(fn, "__name__", "fn"),
                         statistics.median(times), min(times), statistics.fmean(times), repeat)
    if verbose:
        print(result)
    return result


def speed_table(*results: BenchResult):
    """가장 빠른 것 대비 몇 배 느린지 표로 정리한다."""
    from .report import Table
    fastest = min(r.median_ms for r in results)
    table = Table()
    for r in sorted(results, key=lambda r: r.median_ms):
        table.add(name=r.name, median_ms=r.median_ms, x_slower=r.median_ms / fastest if fastest > 0 else float("nan"))
    return table

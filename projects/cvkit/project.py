"""프로젝트 폴더 경로와 설정을 한곳에서 관리한다.

교재 코드는 'images/foo.jpg' 처럼 '현재 작업 폴더' 기준 경로를 써서, 다른 폴더에서 실행하면 깨졌다.
Project 는 스크립트 파일(__file__) 위치를 기준으로 경로를 잡으므로 어디서 실행해도 같다.

    proj = Project(__file__)
    cfg = proj.config                          # config.yaml
    for path in proj.images():                 # data/raw/ 의 이미지들
        ...
    proj.result_path("stages", "a.jpg")        # results/stages/a.jpg (폴더 자동 생성)
"""
from __future__ import annotations

from pathlib import Path

from .config import Config, load_config
from .io import list_images

CONFIG_NAME = "config.yaml"


class Project:
    def __init__(self, file):
        start = Path(file).resolve()
        start = start.parent if start.is_file() or start.suffix else start
        # config.yaml 이 있는 가장 가까운 상위 폴더를 프로젝트 루트로 본다 (src/ 안의 스크립트에서도 동작).
        self.root = next((d for d in (start, *start.parents) if (d / CONFIG_NAME).is_file()), start)
        self.data = self.root / "data"
        self.raw = self.data / "raw"
        self.results = self.root / "results"
        self.config_path = self.root / CONFIG_NAME
        self._config: Config | None = None

    @property
    def name(self) -> str:
        return self.root.name

    @property
    def config(self) -> Config:
        if self._config is None:
            self._config = load_config(self.config_path) if self.config_path.is_file() else Config()
        return self._config

    def path(self, *parts) -> Path:
        """프로젝트 루트 기준 경로. 절대 경로를 주면 그대로 쓴다."""
        return self.root.joinpath(*parts)

    def images(self, folder=None, *, recursive: bool = False) -> list[Path]:
        """이미지 목록. folder 를 생략하면 data/raw/."""
        folder = self.raw if folder is None else self.path(folder)
        return list_images(folder, recursive=recursive)

    def result_path(self, *parts) -> Path:
        """results/ 아래 경로를 만들어 돌려준다 (상위 폴더 자동 생성)."""
        p = self.results.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def __repr__(self) -> str:
        return f"Project(name={self.name!r}, root={str(self.root)!r})"

"""YAML 설정 파일.

파라미터를 코드에 숫자로 박아 두면(매직 넘버) 다른 데이터에서 반드시 깨지고, 무엇을 바꿨는지도 남지 않는다.
config.yaml 에 모아 두고 cfg.params.canny_low 처럼 점으로 꺼내 쓴다.
"""
from __future__ import annotations

from pathlib import Path

import yaml


class Config(dict):
    """점 표기로 접근할 수 있는 dict.  cfg["params"]["k"] == cfg.params.k"""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"설정에 '{key}' 키가 없습니다. 있는 키: {list(self.keys())}") from None

    def __setattr__(self, key, value):
        self[key] = Config.wrap(value)

    @staticmethod
    def wrap(value):
        """안쪽 dict 와 list 속 dict 까지 Config 로 바꾼다."""
        if isinstance(value, dict) and not isinstance(value, Config):
            return Config({k: Config.wrap(v) for k, v in value.items()})
        if isinstance(value, list):
            return [Config.wrap(v) for v in value]
        return value

    def to_dict(self) -> dict:
        def unwrap(v):
            if isinstance(v, dict):
                return {k: unwrap(x) for k, x in v.items()}
            if isinstance(v, list):
                return [unwrap(x) for x in v]
            return v
        return unwrap(self)


def load_config(path) -> Config:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"설정 파일이 없습니다: {path}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"설정 파일 최상위는 key: value 형태여야 합니다: {path}")
    return Config.wrap(data)


def save_config(cfg: dict, path) -> Path:
    """설정을 YAML 로 저장한다. (주석은 보존되지 않는다)"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = cfg.to_dict() if isinstance(cfg, Config) else cfg
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
    return path

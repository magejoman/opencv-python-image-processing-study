# 부록: 디버거에서 `Exception("영상 파일 읽기 오류 발생")`이 날 때

Part 1 진행 중 `02.image_access.py`를 디버거로 실행하다가 생긴 문제와 해결 방법이에요.

## 원인

`imread("images/bright.jpg")`는 **실행할 때의 작업 폴더(cwd)** 기준으로 파일을 찾아요. 확인해 보니 저장소 루트에서 실행하면 `None`이 나고, `chap06`에서 실행하면 정상으로 읽어요.

```
저장소 루트에서 실행 → images/bright.jpg 를 루트에서 찾음 → 없음 → None → Exception
chap06 에서 실행     → chap06/images/bright.jpg 를 찾음   → 있음 → 정상
```

## 설정이 두 군데 있고, 역할이 달라요

- **`.vscode/settings.json`의 `python.terminal.executeInFileDir`**: 터미널에서 Python을 실행할 때만 cwd를 파일 폴더로 맞춰요. **디버거에는 적용되지 않아요.** 여기가 가장 흔한 함정이에요.
- **`.vscode/launch.json`의 `"cwd": "${fileDirname}"`**: 디버거가 cwd를 파일 폴더로 맞춰요. 이 설정이 실제로 디버그에 필요한 부분이에요. 같은 구성에 `PYTHONPATH`(저장소 루트 등)도 들어 있어서 `from Common.histogram import ...`도 동작해요.

## 해결 방법

1. 왼쪽 **Run and Debug**(Ctrl+Shift+D) 패널을 열어요.
2. 상단 드롭다운에서 **`Python: 현재 챕터 파일`**을 선택해요.
3. 디버그할 파일(예: `02.image_access.py`)을 연 상태에서 **F5**를 눌러요.

드롭다운에 다른 항목(예: `Python Debugger: Current File`)이 선택돼 있으면 cwd 설정이 적용되지 않아서 같은 에러가 나요.

## 그래도 안 되면

- `launch.json`의 `cwd`가 `${fileDirname}`인지 다시 확인하세요.
- 디버그 콘솔에 `os.getcwd()`를 찍어 보면 어느 폴더에서 실행됐는지 바로 알 수 있어요.
- `launch.json`은 주석을 허용하는 JSON이라 `//` 주석은 문제가 없어요. 다만 문법 오류가 있으면 드롭다운에 설정이 아예 안 보여요.

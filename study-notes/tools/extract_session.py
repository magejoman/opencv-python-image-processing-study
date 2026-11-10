"""Claude Code 세션 기록(jsonl)에서 '# Part N.' 으로 시작하는 답변을 뽑아 Markdown 파일로 저장한다.

사용법:
    python study-notes/tools/extract_session.py <세션.jsonl> <출력폴더> <챕터폴더이름> [--slug N=이름 ...]

예:
    python study-notes/tools/extract_session.py session.jsonl study-notes/chap06 chap06 \
        --slug 1=pixel-access-lut --slug 2=pixel-value-quantization

동작:
- assistant 메시지의 text 블록만 읽는다 (thinking, tool 호출/결과는 읽지 않는다).
- 줄 시작이 '# Part N.' (또는 '# 📘 LN.', '# Part N · Step ...') 인 위치부터 그 text 블록 끝까지를 N번 Part 로 저장한다.
- '# Part N-M.' 처럼 하위 번호가 있으면 따로 저장한다 (--slug N-M=이름, 파일은 '0N-이름.md').
- 제목 앞에 쓴 글(앞 Part 확인 질문 정답 등)은 버리지 않고 제목 줄 바로 아래로 옮긴다.
- 같은 N 이 여러 번 나오면 가장 긴 것을 쓴다 (다시 쓴 최종본 우선).
  --concat 을 주면 대신 세션 순서대로 '---' 로 이어 붙인다 (한 Part 를 여러 답변에 나눠 쓴 경우, chap07).
- 코드/파일 링크 '](chap06/...)' 를 출력 폴더 기준 상대 경로 '](../../chap06/...)' 로 바꾼다 (다른 chapNN 링크도).
- 콘솔 인코딩 문제를 피하려고 보고서는 ASCII 로만 출력한다.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^# (?:Part |📘 L)(\d+)(?:-(\d+))?(?:\.| ·)", re.M)  # chap12 L0~L3은 '# 📘 LN.', chap09 Part 0은 '# Part 0-M.', chap07은 '# Part N · Step'
LINK_ROOTS = ("Common", "reference", "projects", "moire_sim", "study-notes", ".vscode", "pyproject.toml")
OTHER_CHAPTER = re.compile(r"\]\((chap\d+/)")  # 다른 챕터 링크 (chap07 노트 안의 chap08, chap12)


def extract(jsonl_path, concat=False):
    found, pieces = {}, {}
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") != "assistant":
                continue
            content = d.get("message", {}).get("content")
            if not isinstance(content, list):
                continue
            for b in content:
                if b.get("type") != "text":
                    continue
                text = b["text"]
                m = HEADING.search(text)
                if not m:
                    continue
                n = (int(m.group(1)), int(m.group(2) or 0))     # (Part 번호, 하위 번호 또는 0)
                body = text[m.start():].rstrip() + "\n"
                preamble = text[:m.start()].strip()
                if preamble:                                # 제목 → 앞 Part 정답 → 본문 순서로
                    title, _, rest = body.partition("\n")
                    body = "%s\n\n%s\n\n%s" % (title, preamble, rest.lstrip("\n"))
                if concat:
                    if body not in pieces.setdefault(n, []):
                        pieces[n].append(body)
                elif n not in found or len(body) > len(found[n]):
                    found[n] = body
    if concat:                                              # 한 Part 를 여러 답변에 나눠 쓴 경우: 세션 순서대로 잇는다
        found = {n: "\n---\n\n".join(p) for n, p in pieces.items()}
    return found


def fix_links(body, chapter_dir):
    roots = (chapter_dir,) + LINK_ROOTS
    for r in roots:
        body = body.replace("](%s" % r, "](../../%s" % r)
    return OTHER_CHAPTER.sub(r"](../../\1", body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl")
    ap.add_argument("out_dir")
    ap.add_argument("chapter_dir")
    ap.add_argument("--slug", action="append", default=[], help="N=file-slug")
    ap.add_argument("--concat", action="store_true", help="join every block of a Part in session order")
    args = ap.parse_args()

    slugs = dict(s.split("=", 1) for s in args.slug)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    found = extract(args.jsonl, args.concat)
    for n, sub in sorted(found):
        key = "%d-%d" % (n, sub) if sub else str(n)
        slug = slugs.get(key, "part-%d" % sub if sub else "part")
        name = "%02d-%s.md" % (n, slug)
        body = fix_links(found[(n, sub)], args.chapter_dir)
        (out / name).write_text(body, encoding="utf-8", newline="\n")
        lines = body.splitlines()
        print("part %s -> %s | %d chars | %d lines" % (key, name, len(body), len(lines)))
    nums = {n for n, _ in found}
    missing = [n for n in range(min(nums), max(nums) + 1) if n not in nums] if nums else []
    if missing:
        print("missing parts: %s" % missing)


if __name__ == "__main__":
    sys.exit(main())

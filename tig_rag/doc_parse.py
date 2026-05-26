"""
노하우 가이드 문서(.md) -> 청크.

문서가 ### Q1. / ### A1. 같은 마크다운 헤더로 의미 단위가 나뉘어 있으므로
글자 수가 아니라 헤더(##, ###) 기준으로 분할한다. Q와 A가 중간에 끊기지 않게.
헤더 블록이 너무 길면(MAX_CHUNK_CHARS 초과) 그때만 추가 분할.
"""
import re
from pathlib import Path
from typing import List, Dict

from . import config

_HEADER_RE = re.compile(r"^(#{2,3})\s+(.*)$", re.MULTILINE)


def _split_by_header(text: str) -> List[Dict]:
    """##/### 헤더 위치에서 블록을 나눈다. 각 블록은 헤더 + 본문."""
    matches = list(_HEADER_RE.finditer(text))
    if not matches:
        return [{"heading": "", "body": text.strip()}]

    blocks = []
    # 첫 헤더 이전의 서두(있으면) 포함
    pre = text[: matches[0].start()].strip()
    if pre:
        blocks.append({"heading": "(서두)", "body": pre})

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        heading = m.group(2).strip()
        blocks.append({"heading": heading, "body": block})
    return blocks


def _enforce_max(blocks: List[Dict]) -> List[Dict]:
    """너무 긴 블록만 문자 상한으로 추가 분할."""
    out = []
    for b in blocks:
        body = b["body"]
        if len(body) <= config.MAX_CHUNK_CHARS:
            out.append(b)
            continue
        # 문단 단위로 잘라 상한 이하로 묶기
        paras = body.split("\n\n")
        buf = ""
        for p in paras:
            if len(buf) + len(p) > config.MAX_CHUNK_CHARS and buf:
                out.append({"heading": b["heading"], "body": buf.strip()})
                buf = p
            else:
                buf = f"{buf}\n\n{p}" if buf else p
        if buf.strip():
            out.append({"heading": b["heading"], "body": buf.strip()})
    return out


def chunk_document(path: Path) -> List[Dict]:
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="ignore")
    blocks = _enforce_max(_split_by_header(raw))
    return [
        {
            "text": b["body"],
            "source": path.name,
            "source_type": "document",
            "heading": b["heading"],
            "chunk_index": i,
        }
        for i, b in enumerate(blocks)
        if len(b["body"].strip()) >= 30  # 제목만 있는 서두 등 노이즈 제거
    ]


def chunk_all_documents() -> List[Dict]:
    out = []
    if not config.DOCS_DIR.exists():
        print(f"경고: {config.DOCS_DIR} 없음")
        return out
    for path in sorted(config.DOCS_DIR.glob("*.md")):
        out.extend(chunk_document(path))
    return out

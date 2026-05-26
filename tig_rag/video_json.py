"""
동영상 구간 메타데이터 JSON -> 검색 가능한 청크.

제공자가 영상을 이미 세그먼트(1~2분 단위)로 텍스트화해 줬다.
우리는 Vision 캡셔닝을 하지 않고 이 JSON 을 파싱만 한다.

세그먼트 하나 = 청크 하나.
임베딩 대상 텍스트 = description + transcript + keywords (의미 검색 강화).
metadata(material/pipe_size 등)와 타임스탬프는 메타데이터로만 보관(임베딩 X).
"""
import json
from pathlib import Path
from typing import List, Dict

from . import config


def _seg_to_text(seg: Dict) -> str:
    """검색 품질을 위해 설명/대본/키워드를 합쳐 임베딩 텍스트로."""
    parts = []
    if seg.get("description"):
        parts.append(seg["description"])
    if seg.get("transcript"):
        parts.append(seg["transcript"])
    kws = seg.get("keywords") or []
    if kws:
        parts.append("키워드: " + ", ".join(kws))
    return "\n".join(parts)


def parse_video_json(path: Path) -> List[Dict]:
    """JSON 하나 -> 세그먼트별 청크 리스트."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    video_id = data.get("video_id", Path(path).stem)
    video_title = data.get("video_title", "")
    video_url = data.get("video_url", "")
    vmeta = data.get("metadata", {})

    chunks = []
    for seg in data.get("segments", []):
        chunks.append({
            "text": _seg_to_text(seg),
            "source": video_title or video_id,
            "source_type": "video",
            "video_id": video_id,
            "video_url": video_url,
            "segment_id": seg.get("segment_id"),
            "start_time": seg.get("start_time"),
            "end_time": seg.get("end_time"),
            # 영상 메타: 검색 필터용
            "material": vmeta.get("material"),
            "position": vmeta.get("position"),
            "pipe_size": vmeta.get("pipe_size"),
            "difficulty": vmeta.get("difficulty"),
        })
    return chunks


def parse_all_video_json() -> List[Dict]:
    out = []
    if not config.VIDEO_JSON_DIR.exists():
        print(f"경고: {config.VIDEO_JSON_DIR} 없음")
        return out
    for path in sorted(config.VIDEO_JSON_DIR.glob("*.json")):
        out.extend(parse_video_json(path))
    return out

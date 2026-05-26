"""
지원(시스템 통합) 쪽이 import 해서 쓰는 진입점.

설계 원칙(데이터 제공자 가이드 준수):
  - 답변 본문은 '완결된 기술 설명글'이어야 한다.
  - 본문에 '영상/비디오/유튜브/타임스탬프/몇 분 몇 초/구간' 등의 표현 금지.
  - 영상 세그먼트의 start_time/end_time/video_url 은 답변 텍스트가 아니라
    sources(메타데이터)로만 분리해 내보낸다. 프론트가 영상 점프 링크로 사용.
"""
from typing import Optional, Dict, List

from google import genai
from google.genai import types

from . import config, vectorstore

_genai = genai.Client(api_key=config.GOOGLE_API_KEY)

_SYSTEM = (
    "너는 숙련 파이프 용접공의 노하우를 전수하는 기술 코치다. "
    "제공된 [근거]의 사실만을 토대로 질문에 대한 기술 답변을 명확하고 완결되게 작성하라. "
    "근거에 없는 내용은 지어내지 말고 모른다고 답하라. "
    "흔한 실수나 주의사항이 근거에 있으면 강조하라. "
    "절대 규칙: 답변 본문에 '영상', '비디오', '유튜브', '타임스탬프', "
    "'몇 분 몇 초', '구간', '참고하여 보세요' 등 영상 자료를 가리키는 어떤 표현도 "
    "포함하지 마라. 근거의 자막/설명은 순수한 기술 사실로만 녹여서 일반 설명글로 서술하라."
)


def _build_context(hits: List[Dict]) -> str:
    """LLM 에 넘기는 근거. 출처 라벨에 타임스탬프 등을 넣지 않는다(본문 오염 방지)."""
    blocks = []
    for i, h in enumerate(hits, 1):
        blocks.append(f"[근거 {i}]\n{h['text']}")
    return "\n\n".join(blocks)


def answer_question(
    question: str,
    top_k: int = config.TOP_K,
    source_type: Optional[str] = None,
) -> Dict:
    """
    질문 -> {answer, sources, video_refs}.
      - answer: 영상 언급 없는 순수 기술 설명글
      - sources: 검색에 사용된 근거 메타 (문서/영상 공통)
      - video_refs: 영상 점프용 (video_url, start_time, end_time) — 프론트가 링크로 사용
    """
    hits = vectorstore.query(question, top_k=top_k, source_type=source_type)
    if not hits:
        return {"answer": "관련 노하우를 찾지 못했습니다.", "sources": [], "video_refs": []}

    context = _build_context(hits)
    prompt = f"[근거]\n{context}\n\n[질문]\n{question}"

    resp = _genai.models.generate_content(
        model=config.LLM_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=_SYSTEM),
    )

    sources, video_refs = [], []
    for h in hits:
        sources.append({
            "source": h["source"],
            "source_type": h["source_type"],
            "heading": h.get("heading"),
            "score": h["score"],
        })
        # 영상 근거만 점프 정보 분리
        if h["source_type"] == "video" and h.get("video_url"):
            video_refs.append({
                "video_id": h.get("video_id"),
                "video_url": h.get("video_url"),
                "start_time": h.get("start_time"),
                "end_time": h.get("end_time"),
                "score": h["score"],
            })

    return {"answer": resp.text.strip(), "sources": sources, "video_refs": video_refs}

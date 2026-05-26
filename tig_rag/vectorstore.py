"""
ChromaDB + Google 임베딩(text-embedding-004) — 신 SDK(google-genai) 기준.

문서 청크와 영상 캡션을 같은 컬렉션에 넣되 메타데이터(source_type, timestamp 등)로
구분/필터링 가능하게 한다. 구상도의 '메타데이터 필터링 지원' 박스가 이 부분이다.

주의: ChromaDB 메타데이터 값은 None 을 허용하지 않는다 -> None 은 "" 로 치환.
"""
from typing import List, Dict, Optional

import chromadb
from google import genai
from google.genai import types

from . import config

_genai = genai.Client(api_key=config.GOOGLE_API_KEY)
_client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))


def _get_collection():
    return _client.get_or_create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


_EMBED_BATCH = 100  # Gemini batch embed API 한도


def _embed(texts: List[str], task_type: str) -> List[List[float]]:
    """
    Google 임베딩 호출. task_type 이 검색 품질에 영향:
      - 저장 시: RETRIEVAL_DOCUMENT
      - 질의 시: RETRIEVAL_QUERY
    배치 한도(100)에 맞춰 잘라서 호출한다.
    """
    out: List[List[float]] = []
    for i in range(0, len(texts), _EMBED_BATCH):
        chunk = texts[i:i + _EMBED_BATCH]
        resp = _genai.models.embed_content(
            model=config.EMBEDDING_MODEL,
            contents=chunk,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        out.extend(e.values for e in resp.embeddings)
    return out


def _clean_meta(meta: Dict) -> Dict:
    """ChromaDB 가 None 을 거부하므로 정리. timestamp 등 숫자는 보존."""
    cleaned = {}
    for k, v in meta.items():
        if v is None:
            cleaned[k] = ""
        elif isinstance(v, (str, int, float, bool)):
            cleaned[k] = v
        else:
            cleaned[k] = str(v)
    return cleaned


def index_chunks(chunks: List[Dict]):
    """
    청크 dict 리스트를 임베딩해 ChromaDB 에 저장.
    chunk 스키마는 doc_parse / video_caption 출력 둘 다 수용한다.
    """
    if not chunks:
        print("색인할 청크 없음.")
        return

    col = _get_collection()
    texts = [c["text"] for c in chunks]
    embeddings = _embed(texts, task_type="RETRIEVAL_DOCUMENT")

    ids, metas = [], []
    for i, c in enumerate(chunks):
        stype = c.get("source_type", "document")
        src = c.get("source", "unknown")
        suffix = c.get("chunk_index", c.get("segment_id", i))
        ids.append(f"{stype}::{src}::{suffix}::{i}")
        # 문서/영상 공통 + 각 타입별 메타데이터를 모두 보관.
        # 타임스탬프/영상경로는 답변 본문엔 안 쓰고 sources 로만 내보낸다.
        metas.append(_clean_meta({
            "source": src,
            "source_type": stype,
            "heading": c.get("heading"),
            "video_id": c.get("video_id"),
            "video_url": c.get("video_url"),
            "segment_id": c.get("segment_id"),
            "start_time": c.get("start_time"),
            "end_time": c.get("end_time"),
            "material": c.get("material"),
            "position": c.get("position"),
            "pipe_size": c.get("pipe_size"),
            "difficulty": c.get("difficulty"),
        }))

    col.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metas)
    print(f"{len(chunks)} 청크 색인 완료. 컬렉션 총 {col.count()} 건.")


def query(
    text: str,
    top_k: int = config.TOP_K,
    source_type: Optional[str] = None,
) -> List[Dict]:
    """
    질의 -> 유사 청크 반환.
    source_type 으로 'document'/'video' 필터 가능(메타데이터 필터링).
    """
    col = _get_collection()
    q_emb = _embed([text], task_type="RETRIEVAL_QUERY")[0]

    where = {"source_type": source_type} if source_type else None
    res = col.query(query_embeddings=[q_emb], n_results=top_k, where=where)

    hits = []
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]
    for doc, meta, dist in zip(docs, metas, dists):
        hits.append({
            "text": doc,
            "source": meta.get("source"),
            "source_type": meta.get("source_type"),
            "heading": meta.get("heading") or None,
            "video_id": meta.get("video_id") or None,
            "video_url": meta.get("video_url") or None,
            "start_time": meta.get("start_time") or None,
            "end_time": meta.get("end_time") or None,
            "score": round(1 - dist, 4),
        })
    return hits


def reset_collection():
    """전체 색인 초기화. 재인덱싱 전 호출."""
    try:
        _client.delete_collection(config.COLLECTION_NAME)
    except Exception:
        pass
    _get_collection()
    print("컬렉션 초기화 완료.")

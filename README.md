# TIG 용접 노하우 챗봇 — RAG 모듈 (지율 담당)

노하우 가이드 문서(.md) + 영상 구간 메타데이터(JSON)를 색인하고,
질문에 근거 기반 기술 답변과 영상 점프 참조를 돌려준다.

> 영상은 제공자가 JSON 으로 텍스트화해 줬으므로 **Vision 캡셔닝 안 함.**
> 이 모듈은 파싱 → 청킹 → 임베딩 → ChromaDB 색인 → 검색 파이프라인이다(fine-tuning 아님).

## 데이터 배치 (제공 폴더 그대로)

```
data/
├── 1_용접_기술_가이드_문서/        .md 12종
├── 2_동영상_구간_메타데이터_JSON/   .json 12종
└── 3_시연_동영상_원본/             .mp4 (색인 X, 점프 참조용)
```

## 모듈

| 역할 | 파일 |
|---|---|
| 문서 파싱(헤더 기준 청킹) | `doc_parse.py` |
| 영상 JSON 세그먼트 파싱 | `video_json.py` |
| Gemini 임베딩 + ChromaDB | `vectorstore.py` |
| RAG 답변 생성 (진입점) | `rag_api.py` → `answer_question` |
| 색인 빌드 | `build_index.py` |

## WSL 세팅

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # GOOGLE_API_KEY 채우기
```

## 색인 & 테스트

```bash
python build_index.py --reset
python ask.py "루트 갭은 몇 mm로 맞춰?"
```

## 지원(시스템 통합) 인터페이스

```python
from tig_rag.rag_api import answer_question
r = answer_question("가접 시 용락을 어떻게 방지해?")
# r = {
#   "answer": "...",          # 영상 언급 없는 순수 기술 설명글
#   "sources": [...],         # 근거 메타
#   "video_refs": [{video_url, start_time, end_time, score}, ...]  # 프론트 영상 점프용
# }
```

## 설계 규칙 (제공자 가이드 준수)
- 답변 본문에 '영상/타임스탬프/몇 분 몇 초' 등 표현 금지 → `rag_api._SYSTEM` 에 강제.
- 타임스탬프·영상경로는 본문이 아니라 `video_refs` 로만 분리 출력.
- 문서는 ### Q/A 헤더 단위 청킹, 영상은 세그먼트 단위 청킹.

"""
중앙 설정. 모든 모듈이 여기서 경로/모델명/파라미터를 가져간다.
영상은 제공자가 JSON 메타데이터로 텍스트화해 줬으므로 Vision 캡셔닝은 쓰지 않는다.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- 경로 ---
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# 제공 데이터 폴더 (실제 제공된 구조에 맞춤)
DOCS_DIR = DATA_DIR / "1_용접_기술_가이드_문서"      # 노하우 .md 12종
VIDEO_JSON_DIR = DATA_DIR / "2_동영상_구간_메타데이터_JSON"  # 세그먼트 JSON
VIDEO_SRC_DIR = DATA_DIR / "3_시연_동영상_원본"      # 원본 mp4 (색인 X, 참조용)

CACHE_DIR = DATA_DIR / "cache"
CHROMA_DIR = DATA_DIR / "chroma"

for d in (CACHE_DIR, CHROMA_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --- API 키 ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- 모델 ---
EMBEDDING_MODEL = "gemini-embedding-001"
LLM_MODEL = "gemini-2.5-flash"

# --- 청킹 (문서) ---
# 가이드 문서는 ### Q/A 헤더로 의미 단위가 나뉘므로 헤더 기준 분할.
# 헤더 단위가 너무 길 때만 추가로 자르는 상한.
MAX_CHUNK_CHARS = 1500

# --- 검색 ---
TOP_K = 5

COLLECTION_NAME = "tig_knowhow"

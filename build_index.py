"""
색인 빌드 진입점.
  data/1_용접_기술_가이드_문서/  -> 문서 청크
  data/2_동영상_구간_메타데이터_JSON/ -> 영상 세그먼트 청크
둘 다 ChromaDB 한 컬렉션에 적재(메타데이터로 구분).

사용:
  python build_index.py --reset      # 초기화 후 전체 빌드
  python build_index.py --docs-only
  python build_index.py --videos-only
"""
import argparse

from tig_rag import doc_parse, video_json, vectorstore


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--docs-only", action="store_true")
    ap.add_argument("--videos-only", action="store_true")
    args = ap.parse_args()

    if args.reset:
        vectorstore.reset_collection()

    all_chunks = []
    if not args.videos_only:
        doc_chunks = doc_parse.chunk_all_documents()
        print(f"문서 청크: {len(doc_chunks)}")
        all_chunks += doc_chunks

    if not args.docs_only:
        vid_chunks = video_json.parse_all_video_json()
        print(f"영상 세그먼트 청크: {len(vid_chunks)}")
        all_chunks += vid_chunks

    vectorstore.index_chunks(all_chunks)
    print("\n색인 완료.")


if __name__ == "__main__":
    main()

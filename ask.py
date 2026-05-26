"""
검색/답변 테스트용 CLI.

  python ask.py "루트 갭은 몇 mm로 맞춰?"
  python ask.py "백비드" --video        # 영상 근거만
  python ask.py "퍼징" --docs            # 문서 근거만
"""
import argparse
from tig_rag import rag_api


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--docs", action="store_true")
    ap.add_argument("-k", type=int, default=5)
    args = ap.parse_args()

    stype = "video" if args.video else "document" if args.docs else None
    r = rag_api.answer_question(args.question, top_k=args.k, source_type=stype)

    print("\n=== 답변 ===")
    print(r["answer"])
    print("\n=== 근거 ===")
    for s in r["sources"]:
        h = f" / {s['heading']}" if s.get("heading") else ""
        print(f"- ({s['source_type']}) {s['source']}{h}  유사도={s['score']}")
    if r["video_refs"]:
        print("\n=== 영상 점프 참조 ===")
        for v in r["video_refs"]:
            print(f"- {v['video_url']}  [{v['start_time']}~{v['end_time']}]")


if __name__ == "__main__":
    main()

import argparse
from compiler.common import recommend_nodes, ValidationError
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=int, default=60)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--show-locked", action="store_true")
    args = parser.parse_args()
    try:
        recs = recommend_nodes(minutes=args.minutes, limit=args.limit)
        print("Recommended next")
        print("================")
        if not recs:
            print("No available recommendations.")
            return
        for idx, rec in enumerate(recs, start=1):
            node = rec["node"]
            print(f"{idx}. {node['id']}")
            print(f"   Title: {node.get('title')}")
            print(f"   State: {node.get('state')}")
            print(f"   Score: {rec['score']}")
            print(f"   Why: {rec['reason']}")
    except ValidationError as exc:
        print(f"[INVALID RECOMMENDATION INPUT] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()

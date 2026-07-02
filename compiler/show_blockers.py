from compiler.common import validate_execution, ValidationError
def main():
    try:
        ex = validate_execution()["execution"]
        blockers = [b for b in ex["blockers"] if b.get("status") == "open"]
        print("Open Blockers")
        print("=============")
        if not blockers:
            print("No open blockers.")
            return
        for b in blockers:
            print(f"- {b.get('id')}: {b.get('title')}")
    except ValidationError as exc:
        print(f"[INVALID BLOCKERS VIEW] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()

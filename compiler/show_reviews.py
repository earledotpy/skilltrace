from datetime import date
from compiler.common import validate_execution, ValidationError
def main():
    try:
        ex = validate_execution()["execution"]
        print("Reviews")
        print("=======")
        due = [r for r in ex["reviews"] if r.get("status") == "scheduled" and str(r.get("scheduled_for")) <= date.today().isoformat()]
        upcoming = [r for r in ex["reviews"] if r.get("status") == "scheduled" and str(r.get("scheduled_for")) > date.today().isoformat()]
        print(f"Due: {len(due)}")
        print(f"Upcoming: {len(upcoming)}")
    except ValidationError as exc:
        print(f"[INVALID REVIEWS VIEW] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()

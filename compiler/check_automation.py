import argparse
from compiler.common import validate_policy, ValidationError
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action")
    args = parser.parse_args()
    try:
        p = validate_policy()["policy"]["automation_boundary_policy"]
        rules = {r.get("action"): r for r in p.get("rules", [])}
        rule = rules.get(args.action)
        if not rule:
            print(f"Action: {args.action}")
            print("Permission: forbidden")
            print("Allowed: False")
            print("Requires confirmation: True")
            print("Reason: No rule exists for this automation action.")
            return
        permission = rule.get("permission")
        print(f"Action: {args.action}")
        print(f"Permission: {permission}")
        print(f"Allowed: {permission in {'allowed', 'allowed_with_confirmation'}}")
        print(f"Requires confirmation: {permission in {'allowed_with_confirmation', 'forbidden'}}")
        print(f"Reason: {rule.get('reason')}")
    except ValidationError as exc:
        print(f"[INVALID AUTOMATION CHECK] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()

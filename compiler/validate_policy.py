from compiler.common import validate_policy, print_validation_ok, ValidationError
def main():
    try:
        data = validate_policy()
        p = data["policy"]
        print_validation_ok("Policy layer loaded successfully", Policies=len(p))
        for key, obj in p.items():
            print(f"{key}: {obj.get('id')}")
    except ValidationError as exc:
        print(f"[INVALID POLICY] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()

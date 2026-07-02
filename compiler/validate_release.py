from compiler.common import validate_release, print_validation_ok, ValidationError
def main():
    try:
        r, warnings = validate_release()
        print_validation_ok("Release layer loaded successfully", Release_tests=len(r["tests"]), Smoke_steps=len(r["smoke_test_plan"].get("steps", [])), Criteria=len(r["criteria"]), Test_results=len(r["test_results"]))
        print(f"Project: {r['manifest'].get('project_name')}")
        print(f"Version: {r['manifest'].get('version')}")
        print(f"Status: {r['release_candidate'].get('status')}")
        for warning in warnings:
            print(f"[WARNING] {warning}")
    except ValidationError as exc:
        print(f"[INVALID RELEASE] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()

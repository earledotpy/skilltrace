from compiler.common import validate_evidence, print_validation_ok, ValidationError
def main():
    try:
        ev = validate_evidence()
        e = ev["evidence"]
        print_validation_ok("Evidence layer loaded successfully", Resources=len(e["resources"]), Artifact_specs=len(e["artifact_specs"]), Validation_gates=len(e["validation_gates"]), Attempts=len(e["attempts"]), Evidence_records=len(e["evidence_records"]))
    except ValidationError as exc:
        print(f"[INVALID EVIDENCE] {exc}")
        raise SystemExit(1)
if __name__ == "__main__": main()

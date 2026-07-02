from __future__ import annotations
from datetime import datetime
from pathlib import Path
import subprocess, yaml
from compiler.common import load_release, ValidationError

def run(command: str):
    p = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=45)
    return p.returncode, (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")

def is_mutating(command: str) -> bool:
    markers = ["sync_readiness", "update_state", "plan_session", "record_work", "create_blocker", "create_remediation", "schedule_review", "sqlite_export"]
    return any(m in command for m in markers)

def main():
    release = load_release()
    tests = release["tests"]
    out_dir = Path("release/test_outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    failed_required = []
    print("Release Test Run")
    print("================")
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-mutation", action="store_true")
    args = parser.parse_args()
    for test in tests:
        print()
        print(f"[RUN] {test.get('id')}")
        command = test.get("command")
        if not command:
            status = "skipped"
            summary = "Skipped non-executable test."
            code = None
            output_path = None
        elif is_mutating(command) and not args.allow_mutation:
            status = "skipped"
            summary = "Skipped mutating command because --allow-mutation was not set."
            code = None
            output_path = None
        else:
            code, output = run(command)
            path = out_dir / (test.get("id").replace(".", "_") + ".txt")
            path.write_text(output, encoding="utf-8")
            output_path = str(path)
            if code == 0:
                status = "passed"
                summary = "Command completed successfully."
                print("[PASSED]")
            else:
                status = "failed"
                summary = f"Command failed with exit code {code}."
                print("[FAILED]")
                if test.get("required_for_release", True):
                    failed_required.append(test.get("id"))
        if not command or (is_mutating(command) and not args.allow_mutation):
            print(f"[{status.upper()}]")
        result = {
            "id": "result." + test.get("id").replace("test.", "").replace(".", "-") + "." + datetime.now().strftime("%Y%m%d%H%M%S"),
            "test_id": test.get("id"),
            "status": status,
            "ran_at": datetime.now().isoformat(),
            "exit_code": code,
            "output_path": output_path,
            "summary": summary,
        }
        if status == "failed":
            result["failure_reason"] = summary
        results.append(result)
    Path("release/test_results.yaml").write_text(yaml.safe_dump({"test_results": results}, sort_keys=False), encoding="utf-8")
    print()
    print("Summary")
    print("-------")
    print(f"Passed: {len([r for r in results if r['status']=='passed'])}")
    print(f"Failed: {len([r for r in results if r['status']=='failed'])}")
    print(f"Skipped: {len([r for r in results if r['status']=='skipped'])}")
    if failed_required:
        print("[RELEASE BLOCKED]")
        for item in failed_required:
            print(f"- {item}")
        raise SystemExit(1)
    print("[OK] Release tests completed without required-test failure")

if __name__ == "__main__":
    main()

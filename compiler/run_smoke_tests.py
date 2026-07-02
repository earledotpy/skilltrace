from __future__ import annotations
from pathlib import Path
import subprocess, sys
from compiler.common import load_release, ValidationError

def run(command: str):
    p = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
    return p.returncode, (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")

def main():
    try:
        release = load_release()
        steps = sorted(release["smoke_test_plan"].get("steps", []), key=lambda x: x.get("order", 0))
    except ValidationError as exc:
        print(f"[INVALID SMOKE TEST PLAN] {exc}")
        raise SystemExit(1)
    out_dir = Path("release/smoke_outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    failed = []
    print("Smoke Test Run")
    print("==============")
    for step in steps:
        print()
        print(f"[RUN] {step.get('order')}. {step.get('title')}")
        if step.get("mutates_files"):
            print("[SKIPPED] mutating smoke step")
            continue
        code, output = run(step["command"])
        (out_dir / f"step_{step.get('order')}.txt").write_text(output, encoding="utf-8")
        missing = [s for s in step.get("expected_output_contains", []) if s not in output]
        if code != 0 or missing:
            print("[FAILED]")
            if missing:
                print(f"Missing expected output: {missing}")
            if step.get("required", True):
                failed.append(step.get("title"))
        else:
            print("[PASSED]")
    if failed:
        print("[SMOKE FAILED]")
        for item in failed:
            print(f"- {item}")
        raise SystemExit(1)
    print()
    print("[OK] Smoke tests passed")

if __name__ == "__main__":
    main()

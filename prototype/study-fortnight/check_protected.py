"""Verify protected records are unchanged (contract: before/after hashes)."""
import hashlib
import json
import pathlib

root = pathlib.Path(__file__).resolve().parents[2]
before = json.loads((pathlib.Path(__file__).parent / "protected_hashes_before.json").read_text())
targets = [root / "graph/state.yaml"]
targets += sorted((root / "execution").glob("*.yaml"))
targets += sorted((root / "evidence").glob("*.yaml"))
h = {str(t.relative_to(root)): hashlib.sha256(t.read_bytes()).hexdigest() for t in targets}
diff = [k for k in h if h.get(k) != before.get(k)]
out = pathlib.Path(__file__).parent / "protected_hashes_after.json"
out.write_text(json.dumps(h, indent=2))
print("protected files changed:", diff if diff else "NONE")
print("after hashes written:", out)

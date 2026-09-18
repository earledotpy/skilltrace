"""Find nodes with empty/missing summaries (contract: 'missing summaries' case)."""
import pathlib
import re

nodes = sorted(pathlib.Path(__file__).resolve().parents[2].glob("graph/nodes/**/*.md"))
bad = []
for p in nodes:
    text = p.read_text(encoding="utf-8")
    m = re.search(r"^summary:\s*(.*?)\s*$", text, re.M)
    if m is None:
        bad.append((p.name, "no summary key"))
    else:
        val = m.group(1)
        if val in ('""', "''", "|", ">", "") or val.startswith(("|", ">")) and val.strip(" |>") == "":
            bad.append((p.name, "empty summary"))
print("nodes total:", len(nodes))
print("empty/missing summaries:", len(bad))
for name, why in bad:
    print(" ", name, "-", why)

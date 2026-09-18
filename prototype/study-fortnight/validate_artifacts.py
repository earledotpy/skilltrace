"""Validate the generated artifact and reports."""
import pathlib
import re

here = pathlib.Path(__file__).resolve().parent
page = here.parent / "study-fortnight.html"
text = page.read_text(encoding="utf-8")
print("page bytes:", len(text))
print("replacement chars:", text.count("\ufffd"))
print("step-not-captured placeholders:", text.count("(step not captured)"))
print("engine blocks:", text.count("class='engine'"))
print("proposed mockups:", text.count("class='mock'"))
print("hash ledger verdict:", re.search(r"Protected-record hash ledger.*?<b>(.*?)</b>", text, re.S).group(1))
for name in ["day-reports.md", "branch-coverage.md", "candidate-trigger-matrix.md", "comparisons-and-hazards.md"]:
    p = here / "reports" / name
    t = p.read_text(encoding="utf-8")
    print(f"{name}: {len(t)} bytes, {t.count(chr(10))+1} lines, ufffd={t.count(chr(0xfffd))}")
print("html has <script>:", "<script" in text.lower())
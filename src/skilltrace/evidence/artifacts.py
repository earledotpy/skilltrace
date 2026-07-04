"""Artifact fingerprinting — the content hash a record freezes at submission.

An evidence record fingerprints its artifact *as submitted* (ADR 0003): a
`sha256:<hex>` digest of the file's bytes, frozen into the record and never
touched again. `validate evidence` re-hashes the file at a record's `location`
and warns when it no longer matches — the file drifting afterwards is a health
signal, never a change to acceptance or eligibility (CONTEXT.md).

The digest format is settled here, ahead of `evidence submit` (issue #12), so
both the writer and the drift check agree on one algorithm. `location` is a
repo-relative path; a missing file is a first-class outcome (``None``), not an
error — a learner may reorganize artifacts, and the drift warning is exactly how
that surfaces.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

# The one digest algorithm records commit to; the prefix makes the scheme
# explicit in the stored value, so a future migration to another algorithm is a
# readable change rather than an ambiguous hex blob.
_ALGORITHM = "sha256"


def hash_artifact(path: Path | str) -> str:
    """Return ``sha256:<hex>`` over the bytes of the file at `path`.

    Raises `OSError` if the file cannot be read — the caller decides whether an
    unreadable artifact is a missing-file outcome (drift) or a hard error
    (submission). Reads in chunks so a large artifact does not load whole.
    """
    digest = hashlib.new(_ALGORITHM)
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return f"{_ALGORITHM}:{digest.hexdigest()}"


def probe_hash(root: Path | str, location: str) -> str | None:
    """Current ``sha256:<hex>`` of the artifact at repo-relative `location`.

    Returns ``None`` when nothing readable is at `location` (absent, or a
    directory) — the drift check reads that as a missing artifact. Any other
    read error also becomes ``None``: for a health warning, "cannot fingerprint
    it" and "it is gone" are the same signal.
    """
    path = Path(root) / location
    if not path.is_file():
        return None
    try:
        return hash_artifact(path)
    except OSError:
        return None

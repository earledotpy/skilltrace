"""Artifact fingerprinting: the real hash + drift probe (issue #11).

The drift unit tests in test_validation.py inject a fake probe, so this is the
one place the actual `hash_artifact` / file-resolution path is exercised: a
matching file, a modified file, and a missing file.
"""

from __future__ import annotations

from skilltrace.evidence.artifacts import hash_artifact, probe_hash


def test_hash_is_stable_and_prefixed(tmp_path):
    artifact = tmp_path / "a.md"
    artifact.write_text("hello evidence", encoding="utf-8")
    digest = hash_artifact(artifact)
    assert digest.startswith("sha256:")
    assert digest == hash_artifact(artifact)  # deterministic


def test_hash_changes_with_content(tmp_path):
    artifact = tmp_path / "a.md"
    artifact.write_text("one", encoding="utf-8")
    first = hash_artifact(artifact)
    artifact.write_text("two", encoding="utf-8")
    assert hash_artifact(artifact) != first


def test_probe_matches_recorded_hash(tmp_path):
    (tmp_path / "evidence").mkdir()
    artifact = tmp_path / "evidence" / "a.md"
    artifact.write_text("frozen at submission", encoding="utf-8")
    recorded = hash_artifact(artifact)
    assert probe_hash(tmp_path, "evidence/a.md") == recorded


def test_probe_reflects_a_modified_file(tmp_path):
    (tmp_path / "evidence").mkdir()
    artifact = tmp_path / "evidence" / "a.md"
    artifact.write_text("original", encoding="utf-8")
    recorded = hash_artifact(artifact)
    artifact.write_text("drifted", encoding="utf-8")
    assert probe_hash(tmp_path, "evidence/a.md") != recorded


def test_probe_missing_file_is_none(tmp_path):
    assert probe_hash(tmp_path, "evidence/gone.md") is None


def test_probe_directory_is_none(tmp_path):
    (tmp_path / "evidence").mkdir()
    assert probe_hash(tmp_path, "evidence") is None

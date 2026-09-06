"""`validate policy` — v2.0 portfolio seed value-range checks (spec §7.2)."""

from __future__ import annotations

import yaml

from skilltrace import cli


def _set_portfolio_field(root, key: str, value) -> None:
    path = root / "policy" / "portfolio.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["portfolio_policy"][key] = value
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def test_shipped_portfolio_seed_validates_clean(policy_repo, capsys):
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 0
    assert "validate policy: OK" in capsys.readouterr().out


def test_portfolio_seed_defaults_match_spec(policy_repo):
    doc = yaml.safe_load(
        (policy_repo / "policy" / "portfolio.yaml").read_text(encoding="utf-8")
    )["portfolio_policy"]
    assert doc["default_track"] == "portfolio"
    assert doc["default_format"] == "md"
    assert doc["resource_staleness_days"] == 90


def test_portfolio_bad_default_track_fails(policy_repo, capsys):
    _set_portfolio_field(policy_repo, "default_track", "")
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    assert "default_track" in capsys.readouterr().out


def test_portfolio_bad_default_format_fails(policy_repo, capsys):
    _set_portfolio_field(policy_repo, "default_format", "pdf")
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    assert "default_format" in capsys.readouterr().out


def test_portfolio_bad_staleness_window_fails(policy_repo, capsys):
    _set_portfolio_field(policy_repo, "resource_staleness_days", 0)
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    assert "resource_staleness_days" in capsys.readouterr().out


def test_missing_portfolio_seed_fails(policy_repo, capsys):
    (policy_repo / "policy" / "portfolio.yaml").unlink()
    rc = cli.run(["validate", "policy"], root=policy_repo)
    assert rc == 1
    assert "portfolio.yaml" in capsys.readouterr().out

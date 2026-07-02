
from __future__ import annotations

from pathlib import Path
from datetime import date, datetime
import argparse
import json
import sqlite3
import subprocess
import sys

import yaml


class ValidationError(Exception):
    pass


def root() -> Path:
    return Path.cwd()


def load_yaml(path: Path):
    if not path.exists():
        raise ValidationError(f"Missing file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValidationError(f"YAML root must be an object: {path}")
    return data


def load_list_file(path: Path, key: str) -> list:
    data = load_yaml(path)
    items = data.get(key, [])
    if not isinstance(items, list):
        raise ValidationError(f"{path} must contain list key '{key}'")
    return items


def parse_node_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValidationError(f"Node file missing YAML frontmatter: {path}")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValidationError(f"Malformed frontmatter: {path}")
    data = yaml.safe_load(parts[1]) or {}
    if not isinstance(data, dict):
        raise ValidationError(f"Node frontmatter must be object: {path}")
    data["_path"] = str(path)
    return data


def load_nodes(project_root: Path | None = None) -> list[dict]:
    project_root = project_root or root()
    nodes_dir = project_root / "graph" / "nodes"
    if not nodes_dir.exists():
        raise ValidationError("Missing graph/nodes directory")
    nodes = [parse_node_file(path) for path in sorted(nodes_dir.glob("*.md"))]
    if not nodes:
        raise ValidationError("No graph nodes found")
    return nodes


def load_edges(project_root: Path | None = None) -> list[dict]:
    project_root = project_root or root()
    return load_list_file(project_root / "graph" / "edges.yaml", "edges")


def node_id_set(project_root: Path | None = None) -> set[str]:
    return {node["id"] for node in load_nodes(project_root)}


def validate_graph(project_root: Path | None = None) -> dict:
    project_root = project_root or root()
    nodes = load_nodes(project_root)
    edges = load_edges(project_root)

    ids = [node.get("id") for node in nodes]
    if len(ids) != len(set(ids)):
        raise ValidationError("Duplicate node IDs found")

    node_ids = set(ids)
    for node in nodes:
        if not node.get("title"):
            raise ValidationError(f"Node missing title: {node.get('id')}")
        if not node.get("state"):
            raise ValidationError(f"Node missing state: {node.get('id')}")
        for anchor in node.get("roadmap_anchors", []) or []:
            if anchor.get("source_role") != "reference_only":
                raise ValidationError(f"Roadmap anchor is not reference_only: {node.get('id')}")

    edge_ids = [edge.get("id") for edge in edges]
    if len(edge_ids) != len(set(edge_ids)):
        raise ValidationError("Duplicate edge IDs found")

    hard_adj: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if source not in node_ids:
            raise ValidationError(f"Edge source missing node: {edge.get('id')} -> {source}")
        if target not in node_ids:
            raise ValidationError(f"Edge target missing node: {edge.get('id')} -> {target}")
        if edge.get("edge_type") == "hard_prerequisite" and edge.get("active", True):
            if float(edge.get("strength", 0)) != 1.0:
                raise ValidationError(f"Hard prerequisite must have strength 1.0: {edge.get('id')}")
            if edge.get("can_override") is not False:
                raise ValidationError(f"Hard prerequisite cannot be overrideable: {edge.get('id')}")
            hard_adj[source].append(target)

    seen = set()
    stack = set()

    def dfs(node_id: str):
        if node_id in stack:
            raise ValidationError("Cycle detected in hard-prerequisite graph")
        if node_id in seen:
            return
        stack.add(node_id)
        for nxt in hard_adj.get(node_id, []):
            dfs(nxt)
        stack.remove(node_id)
        seen.add(node_id)

    for node_id in node_ids:
        dfs(node_id)

    state_counts: dict[str, int] = {}
    for node in nodes:
        state = node.get("state", "unknown")
        state_counts[state] = state_counts.get(state, 0) + 1

    return {"nodes": nodes, "edges": edges, "state_counts": state_counts}


def load_evidence(project_root: Path | None = None) -> dict:
    project_root = project_root or root()
    evidence_dir = project_root / "evidence"
    return {
        "resources": load_list_file(evidence_dir / "resources.yaml", "resources"),
        "artifact_specs": load_list_file(evidence_dir / "artifact_specs.yaml", "artifact_specs"),
        "validation_gates": load_list_file(evidence_dir / "validation_gates.yaml", "validation_gates"),
        "attempts": load_list_file(evidence_dir / "attempts.yaml", "attempts"),
        "evidence_records": load_list_file(evidence_dir / "evidence_records.yaml", "evidence_records"),
    }


def validate_evidence(project_root: Path | None = None) -> dict:
    project_root = project_root or root()
    graph = validate_graph(project_root)
    node_ids = {node["id"] for node in graph["nodes"]}
    evidence = load_evidence(project_root)

    for key in ["artifact_specs", "validation_gates", "attempts", "evidence_records"]:
        ids = [item.get("id") for item in evidence[key] if item.get("id")]
        if len(ids) != len(set(ids)):
            raise ValidationError(f"Duplicate IDs in evidence/{key}")

    for spec in evidence["artifact_specs"]:
        if spec.get("node_id") not in node_ids:
            raise ValidationError(f"Artifact spec references missing node: {spec.get('id')} -> {spec.get('node_id')}")

    for gate in evidence["validation_gates"]:
        if gate.get("node_id") not in node_ids:
            raise ValidationError(f"Validation gate references missing node: {gate.get('id')} -> {gate.get('node_id')}")
        if gate.get("gate_kind") in {"pytest", "objective_eval", "nbgrader"} and not gate.get("command"):
            raise ValidationError(f"Executable gate missing command: {gate.get('id')}")
        if gate.get("ai_advisory_only") and gate.get("can_close_node"):
            raise ValidationError(f"AI advisory gate cannot close node: {gate.get('id')}")

    gate_ids = {gate.get("id") for gate in evidence["validation_gates"]}
    spec_ids = {spec.get("id") for spec in evidence["artifact_specs"]}

    for attempt in evidence["attempts"]:
        if attempt.get("node_id") not in node_ids:
            raise ValidationError(f"Attempt references missing node: {attempt.get('id')}")
        if attempt.get("gate_id") and attempt.get("gate_id") not in gate_ids:
            raise ValidationError(f"Attempt references missing gate: {attempt.get('id')} -> {attempt.get('gate_id')}")

    for record in evidence["evidence_records"]:
        if record.get("node_id") not in node_ids:
            raise ValidationError(f"Evidence record references missing node: {record.get('id')}")
        if record.get("gate_id") and record.get("gate_id") not in gate_ids:
            raise ValidationError(f"Evidence record references missing gate: {record.get('id')}")
        if record.get("artifact_spec_id") and record.get("artifact_spec_id") not in spec_ids:
            raise ValidationError(f"Evidence record references missing artifact spec: {record.get('id')}")
        if record.get("review_authority") == "ai_advisory":
            raise ValidationError(f"AI advisory cannot be acceptance authority: {record.get('id')}")

    return {"graph": graph, "evidence": evidence}


def load_execution(project_root: Path | None = None) -> dict:
    project_root = project_root or root()
    execution_dir = project_root / "execution"
    return {
        "sessions": load_list_file(execution_dir / "sessions.yaml", "sessions"),
        "session_work": load_list_file(execution_dir / "session_work.yaml", "session_work"),
        "blockers": load_list_file(execution_dir / "blockers.yaml", "blockers"),
        "remediation_actions": load_list_file(execution_dir / "remediation_actions.yaml", "remediation_actions"),
        "reviews": load_list_file(execution_dir / "reviews.yaml", "reviews"),
        "events": load_list_file(execution_dir / "events.yaml", "events"),
    }


def validate_execution(project_root: Path | None = None) -> dict:
    project_root = project_root or root()
    ev = validate_evidence(project_root)
    node_ids = {node["id"] for node in ev["graph"]["nodes"]}
    execution = load_execution(project_root)

    for key, items in execution.items():
        ids = [item.get("id") for item in items if item.get("id")]
        if len(ids) != len(set(ids)):
            raise ValidationError(f"Duplicate IDs in execution/{key}")

    session_ids = {session.get("id") for session in execution["sessions"]}
    for item in execution["session_work"]:
        if item.get("node_id") not in node_ids:
            raise ValidationError(f"Session work references missing node: {item.get('id')}")
        if session_ids and item.get("session_id") not in session_ids:
            raise ValidationError(f"Session work references missing session: {item.get('id')}")

    for blocker in execution["blockers"]:
        if blocker.get("node_id") not in node_ids:
            raise ValidationError(f"Blocker references missing node: {blocker.get('id')}")

    for action in execution["remediation_actions"]:
        node_id = action.get("target_node_id") or action.get("node_id")
        if node_id and node_id not in node_ids:
            raise ValidationError(f"Remediation references missing node: {action.get('id')}")

    for review in execution["reviews"]:
        if review.get("node_id") not in node_ids:
            raise ValidationError(f"Review references missing node: {review.get('id')}")

    return {"graph": ev["graph"], "evidence": ev["evidence"], "execution": execution}


def load_interface(project_root: Path | None = None) -> dict:
    project_root = project_root or root()
    interface_dir = project_root / "interface"
    return {
        "commands": load_list_file(interface_dir / "commands.yaml", "commands"),
        "views": load_list_file(interface_dir / "views.yaml", "views"),
        "cards": load_list_file(interface_dir / "cards.yaml", "cards"),
        "state": load_yaml(interface_dir / "state.yaml").get("state", {}),
    }


def validate_interface(project_root: Path | None = None) -> dict:
    project_root = project_root or root()
    graph = validate_graph(project_root)
    node_ids = {node["id"] for node in graph["nodes"]}
    interface = load_interface(project_root)

    commands = interface["commands"]
    views = interface["views"]
    cards = interface["cards"]

    command_ids = [cmd.get("id") for cmd in commands]
    view_ids = [view.get("id") for view in views]
    if len(command_ids) != len(set(command_ids)):
        raise ValidationError("Duplicate interface command IDs found")
    if len(view_ids) != len(set(view_ids)):
        raise ValidationError("Duplicate interface view IDs found")

    command_set = set(command_ids)
    action_ids: set[str] = set()
    for view in views:
        primary = view.get("primary_command_id")
        if primary and primary not in command_set:
            raise ValidationError(f"View references missing command: {view.get('id')} -> {primary}")
        for action in view.get("actions", []) or []:
            aid = action.get("id")
            if aid in action_ids:
                raise ValidationError(f"Duplicate action ID: {aid}")
            action_ids.add(aid)
            cid = action.get("command_id")
            if cid and cid not in command_set:
                raise ValidationError(f"Action references missing command: {aid} -> {cid}")

    view_set = set(view_ids)
    for card in cards:
        if card.get("view_id") not in view_set:
            raise ValidationError(f"Card references missing view: {card.get('id')}")
        if card.get("node_id") and card.get("node_id") not in node_ids:
            raise ValidationError(f"Card references missing node: {card.get('id')}")
        for aid in card.get("action_ids", []) or []:
            if aid not in action_ids:
                raise ValidationError(f"Card references missing action: {card.get('id')} -> {aid}")

    active_view = interface.get("state", {}).get("active_view_id")
    if active_view and active_view not in view_set:
        raise ValidationError(f"Interface state references missing active view: {active_view}")

    return {"graph": graph, "interface": interface}


def load_policy(project_root: Path | None = None) -> dict:
    project_root = project_root or root()
    policy_dir = project_root / "policy"
    names = {
        "recommendation_policy": "recommendation.yaml",
        "remediation_policy": "remediation.yaml",
        "review_cadence_policy": "review_cadence.yaml",
        "mastery_promotion_policy": "mastery_promotion.yaml",
        "automation_boundary_policy": "automation_boundary.yaml",
        "workload_policy": "workload.yaml",
    }
    return {key: load_yaml(policy_dir / filename).get(key, {}) for key, filename in names.items()}


def validate_policy(project_root: Path | None = None) -> dict:
    project_root = project_root or root()
    validate_interface(project_root)
    validate_execution(project_root)
    policy = load_policy(project_root)

    rec = policy["recommendation_policy"]
    factors = [w.get("factor") for w in rec.get("weights", []) if w.get("enabled", True)]
    for required in ["prerequisite_readiness", "track_priority", "downstream_leverage"]:
        if required not in factors:
            raise ValidationError(f"Recommendation policy missing required factor: {required}")

    automation = policy["automation_boundary_policy"]
    permissions = {rule.get("action"): rule.get("permission") for rule in automation.get("rules", [])}
    for action in ["pass_node", "master_node", "delete_record"]:
        if permissions.get(action) != "forbidden":
            raise ValidationError(f"Automation action must be forbidden: {action}")

    mastery = policy["mastery_promotion_policy"]
    if mastery.get("allow_ai_review_as_mastery_authority"):
        raise ValidationError("AI review cannot be mastery authority")
    if mastery.get("allow_mastery_from_single_session"):
        raise ValidationError("Mastery cannot be granted from one session")

    review = policy["review_cadence_policy"]
    if automation.get("require_review_for_mastery") and not review.get("schedule_reviews_after_pass"):
        raise ValidationError("Review for mastery is required but review scheduling is disabled")

    workload = policy["workload_policy"]
    limit_kinds = {item.get("limit_kind") for item in workload.get("limits", [])}
    if "session_minutes" not in limit_kinds:
        raise ValidationError("Workload policy missing session_minutes limit")

    return {"policy": policy}


def load_release(project_root: Path | None = None) -> dict:
    project_root = project_root or root()
    release_dir = project_root / "release"
    return {
        "manifest": load_yaml(release_dir / "manifest.yaml").get("manifest", {}),
        "tests": load_yaml(release_dir / "tests.yaml").get("tests", []),
        "smoke_test_plan": load_yaml(release_dir / "smoke_tests.yaml").get("smoke_test_plan", {}),
        "criteria": load_yaml(release_dir / "criteria.yaml").get("criteria", []),
        "release_candidate": load_yaml(release_dir / "release_candidate.yaml").get("release_candidate", {}),
        "test_results": load_yaml(release_dir / "test_results.yaml").get("test_results", []),
    }


def validate_release(project_root: Path | None = None) -> tuple[dict, list[str]]:
    project_root = project_root or root()
    release = load_release(project_root)
    warnings: list[str] = []

    manifest = release["manifest"]
    for item in manifest.get("required_paths", []):
        if item.get("required", True) and not (project_root / item.get("path", "")).exists():
            raise ValidationError(f"Missing required release path: {item.get('path')}")

    tests = release["tests"]
    if not tests:
        raise ValidationError("Release test matrix is empty")
    test_ids = {test.get("id") for test in tests}
    required_ids = {test.get("id") for test in tests if test.get("required_for_release", True)}
    if not required_ids:
        raise ValidationError("No required release tests found")

    commands = [test.get("command") for test in tests if test.get("command")]
    if len(commands) != len(set(commands)):
        raise ValidationError("Duplicate release test commands found")

    plan = release["smoke_test_plan"]
    steps = plan.get("steps", [])
    if not steps:
        raise ValidationError("Smoke test plan is empty")
    for step in steps:
        if step.get("required", True) and step.get("mutates_files"):
            raise ValidationError(f"Required smoke test mutates files: {step.get('title')}")

    for criterion in release["criteria"]:
        missing = set(criterion.get("related_test_ids", []) or []) - test_ids
        if missing:
            raise ValidationError(f"Criterion references missing tests: {criterion.get('id')} -> {sorted(missing)}")

    results = release["test_results"]
    result_test_ids = {result.get("test_id") for result in results}
    missing_required_results = required_ids - result_test_ids
    if missing_required_results:
        warnings.append(f"Required tests have no recorded result: {sorted(missing_required_results)}")

    for result in results:
        if result.get("test_id") in required_ids and result.get("status") == "failed":
            raise ValidationError(f"Required release test failed: {result.get('test_id')}")

    rc = release["release_candidate"]
    required_layers = {
        "layer_1_graph", "layer_2_evidence", "layer_3_execution",
        "layer_4_interface", "layer_5_policy", "layer_6_release",
    }
    included = set(rc.get("included_layers", []) or [])
    missing_layers = required_layers - included
    if missing_layers:
        raise ValidationError(f"Release candidate missing layers: {sorted(missing_layers)}")

    return release, warnings


def print_validation_ok(label: str, **counts):
    print(f"[VALID] {label}")
    for key, value in counts.items():
        print(f"{key}: {value}")


def state_counts(nodes: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in nodes:
        s = node.get("state", "unknown")
        counts[s] = counts.get(s, 0) + 1
    return counts


def recommend_nodes(project_root: Path | None = None, minutes: int = 60, limit: int = 5) -> list[dict]:
    graph = validate_graph(project_root)
    nodes = graph["nodes"]
    edges = graph["edges"]
    node_by_id = {node["id"]: node for node in nodes}
    incoming: dict[str, list[dict]] = {node["id"]: [] for node in nodes}
    outgoing_count: dict[str, int] = {node["id"]: 0 for node in nodes}
    for edge in edges:
        incoming.setdefault(edge.get("target"), []).append(edge)
        outgoing_count[edge.get("source")] = outgoing_count.get(edge.get("source"), 0) + 1

    def hard_satisfied(node):
        for edge in incoming.get(node["id"], []):
            if edge.get("edge_type") != "hard_prerequisite":
                continue
            source_node = node_by_id[edge.get("source")]
            if source_node.get("state") not in {"passed", "mastered"}:
                return False
        return True

    track_bonus = {
        "remediation": 8, "foundational": 6, "core": 5,
        "portfolio": 4, "systems": 3, "contextual": 2, "preview": 1,
    }

    candidates = []
    for node in nodes:
        if node.get("state") not in {"available", "active"}:
            continue
        if not hard_satisfied(node):
            continue
        score = track_bonus.get(node.get("track"), 0) + outgoing_count.get(node["id"], 0)
        fit = node.get("micro_session_fit") or {}
        if minutes <= 15 and fit.get("can_fit_15_min"):
            score += 2
        elif minutes <= 30 and fit.get("can_fit_30_min"):
            score += 1
        if node.get("state") == "active":
            score += 2
        candidates.append({"node": node, "score": score, "reason": "available, prerequisite-safe, and useful for downstream progress"})
    return sorted(candidates, key=lambda item: item["score"], reverse=True)[:limit]


def sqlite_export_all(project_root: Path | None = None) -> Path:
    project_root = project_root or root()
    graph = validate_graph(project_root)
    ev = validate_evidence(project_root)
    ex = validate_execution(project_root)
    interface = validate_interface(project_root)
    policy = validate_policy(project_root)

    db_path = project_root / "data" / "skill_graph.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        with conn:
            conn.executescript("""
            DROP TABLE IF EXISTS graph_nodes;
            DROP TABLE IF EXISTS graph_edges;
            DROP TABLE IF EXISTS artifact_specs;
            DROP TABLE IF EXISTS validation_gates;
            DROP TABLE IF EXISTS interface_commands;
            DROP TABLE IF EXISTS policy_registry;
            CREATE TABLE graph_nodes (id TEXT PRIMARY KEY, title TEXT, state TEXT, payload_json TEXT);
            CREATE TABLE graph_edges (id TEXT PRIMARY KEY, source TEXT, target TEXT, edge_type TEXT, payload_json TEXT);
            CREATE TABLE artifact_specs (id TEXT PRIMARY KEY, node_id TEXT, payload_json TEXT);
            CREATE TABLE validation_gates (id TEXT PRIMARY KEY, node_id TEXT, payload_json TEXT);
            CREATE TABLE interface_commands (id TEXT PRIMARY KEY, name TEXT, module_path TEXT, payload_json TEXT);
            CREATE TABLE policy_registry (id TEXT PRIMARY KEY, policy_type TEXT, payload_json TEXT);
            """)
            for node in graph["nodes"]:
                payload = dict(node)
                payload.pop("_path", None)
                conn.execute("INSERT INTO graph_nodes VALUES (?, ?, ?, ?)", (node["id"], node.get("title"), node.get("state"), json.dumps(payload, default=str)))
            for edge in graph["edges"]:
                conn.execute("INSERT INTO graph_edges VALUES (?, ?, ?, ?, ?)", (edge.get("id"), edge.get("source"), edge.get("target"), edge.get("edge_type"), json.dumps(edge, default=str)))
            for spec in ev["evidence"]["artifact_specs"]:
                conn.execute("INSERT INTO artifact_specs VALUES (?, ?, ?)", (spec.get("id"), spec.get("node_id"), json.dumps(spec, default=str)))
            for gate in ev["evidence"]["validation_gates"]:
                conn.execute("INSERT INTO validation_gates VALUES (?, ?, ?)", (gate.get("id"), gate.get("node_id"), json.dumps(gate, default=str)))
            for cmd in interface["interface"]["commands"]:
                conn.execute("INSERT INTO interface_commands VALUES (?, ?, ?, ?)", (cmd.get("id"), cmd.get("name"), cmd.get("module_path"), json.dumps(cmd, default=str)))
            for key, obj in policy["policy"].items():
                conn.execute("INSERT INTO policy_registry VALUES (?, ?, ?)", (obj.get("id"), key, json.dumps(obj, default=str)))
    finally:
        conn.close()
    return db_path


def run_shell(command: str, cwd: Path | None = None, timeout: int = 30) -> tuple[int, str]:
    p = subprocess.run(command, shell=True, cwd=str(cwd or root()), text=True, capture_output=True, timeout=timeout)
    output = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
    return p.returncode, output

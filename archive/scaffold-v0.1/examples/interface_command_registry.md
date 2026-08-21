# Interface Command Registry

This file summarizes the Layer 4D CLI-first interface registry.

## Core operating loop

```bash
python -m compiler.show_system_health
python -m compiler.show_home
python -m compiler.recommend_next --minutes 60 --limit 5 --show-locked
python -m compiler.plan_session standard 60 math.arithmetic.order_operations_01 --goal "Complete one short problem set"
python -m compiler.record_work <session_id> math.arithmetic.order_operations_01 progressed 55 --notes "Completed one set."
python -m compiler.show_evidence_status --node-id math.arithmetic.order_operations_01
python -m compiler.check_pass_eligibility math.arithmetic.order_operations_01
```

## Policy

Read-only commands inspect state.
Mutating commands append or update local YAML files.
No command silently passes or masters a node.
Dashboard cards are attention surfaces, not automatic state transitions.

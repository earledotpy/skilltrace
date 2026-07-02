# Runbook

Recommended daily loop:

```bash
python -m compiler.show_system_health
python -m compiler.show_home
python -m compiler.recommend_next --minutes 60 --limit 5 --show-locked
python -m compiler.show_node_detail math.arithmetic.order_operations_01
python -m compiler.show_evidence_status --node-id math.arithmetic.order_operations_01
```

Policy checks:

```bash
python -m compiler.check_automation pass_node
python -m compiler.check_automation master_node
python -m compiler.check_automation delete_record
```

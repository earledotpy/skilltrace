# Policy Command Flow

This flow is advisory. Policy commands do not silently pass, master, or delete records.

```bash
python -m compiler.validate_policy
python -m compiler.check_automation pass_node
python -m compiler.suggest_remediation
python -m compiler.suggest_reviews
python -m compiler.check_mastery_eligibility math.arithmetic.order_operations_01
```

Expected boundary:

- `recommend_node` may be automated because it is advisory.
- `sync_readiness` requires confirmation.
- `create_review` requires confirmation.
- `create_remediation` requires confirmation.
- `pass_node` is forbidden for automation.
- `master_node` is forbidden for automation.
- `delete_record` is forbidden.

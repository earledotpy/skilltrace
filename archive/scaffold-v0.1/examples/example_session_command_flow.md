# Example Session Command Flow

This is illustrative only; it is not an active execution record.

```bash
python -m compiler.recommend_next --minutes 60 --show-locked

python -m compiler.plan_session standard 60 math.arithmetic.order_operations_01 \
  --goal "Complete one short order-of-operations problem set" \
  --energy 3 \
  --confidence 2

python -m compiler.record_work session.20260628.190000 math.arithmetic.order_operations_01 progressed 55 \
  --notes "Completed one short set; nested-parentheses mistakes remain." \
  --next-action "Do a focused nested-parentheses set."

python -m compiler.create_blocker math.arithmetic.order_operations_01 conceptual \
  "Nested parentheses confusion" \
  "Repeated mistakes when expressions contained nested parentheses." \
  --severity 2 \
  --next-action "Create a focused remediation set."

python -m compiler.create_remediation math.arithmetic.order_operations_01 practice_set \
  "Nested-parentheses practice" \
  "Complete a focused 10-question set on nested parentheses." \
  --planned-minutes 20 \
  --due-in-days 1

python -m compiler.schedule_review math.arithmetic.order_operations_01 spaced_recall \
  "Solve five order-of-operations problems without notes and explain one correction." \
  --in-days 3 \
  --expected-minutes 15
```

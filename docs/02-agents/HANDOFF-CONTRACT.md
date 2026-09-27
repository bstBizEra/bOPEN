# Handoff Contract

Every handoff contains:

```yaml
handoff_id:
work_item_id:
from_actor:
to_actor:
role_completed:
repository:
branch:
worktree:
base_commit:
head_commit:
requirements:
decisions:
changed_files:
commands_run:
tests:
evidence_paths:
findings:
residual_risks:
blocked_items:
recommended_next_action:
authorization_required:
timestamp:
```

The receiver must verify repository state and evidence rather than trust the narrative
summary.

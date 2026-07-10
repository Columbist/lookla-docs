# Architecture Reviews

Diff files for each implemented backlog task, preserved for historical reference.

Each `.diff` file represents the full `git diff main...feat/T-NNN-*` at the moment
the branch was submitted for architectural review.

| Task | File | Description | Status |
|---|---|---|---|
| T-001 | [T-001.diff](T-001.diff) | Alembic baseline setup | Merged — Approved 10/10 |
| T-002 | [T-002.diff](T-002.diff) | Add address_district column + index | In review |

## Review workflow

```
Claude implements task (feat/T-NNN-* branch)
  → local tests pass
  → CI passes
  → git diff main...HEAD saved here as T-NNN.diff
  → architectural review (ChatGPT or human reviewer)
  → fixes applied if needed
  → merge to main
```

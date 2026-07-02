# Issues

File-based issue tracker (local-first, like everything else here). One file
per issue: `NNNN-short-slug.md`, numbered sequentially, never reused.

Frontmatter:

```yaml
---
id: 3
title: Edge loader and pruned edge schema
milestone: v0.3.0-rc1        # roadmap RC this belongs to
labels: [graph, migration]
status: open                 # open | in_progress | done | wontfix
depends_on: [1]              # issue ids that must land first
---
```

Conventions:

- Milestones are the roadmap RC names; an issue belongs to exactly one.
- Each issue carries its own acceptance criteria, including tests — an
  issue without green tests is not done (TDD: write the failing test first).
- Safety rules in `CLAUDE.md` apply to every issue; no issue may introduce
  an automated pass/master/delete path.
- Close by setting `status: done` and appending a short outcome note; files
  are never deleted.

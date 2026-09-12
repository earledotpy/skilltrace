# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues. Use the gh CLI for all operations.

## Editing issue bodies safely

Issue bodies and comments carry typographic punctuation by convention (em dashes,
arrows, `§`, `…`, `→`). **Never write a body through PowerShell text capture**
(`>`, `Out-File`, `Set-Content`): it replaces every non-ASCII character with `?` or
U+FFFD, silently corrupting a map that later sessions must then read and repair
(map #208 lost 140 characters this way). Use a byte-preserving path instead: fetch
with `gh issue view <n> --json body --jq .body` into a UTF-8 file via Python, edit the
file, push with `gh issue edit <n> --body-file <file>`. Before pushing, assert
`body.count("\ufffd") == 0`.

## Wayfinding operations

How wayfinder maps (`wayfinder:map`) and their tickets are expressed in this repo.
The v2.4 interface-direction map is the worked example of all of it; its own
`## Notes` states the core conventions ("ticket bodies carry `Part of wayfinder map`
+ `Blocked by` references, assignee = claim").

- **Labels.** Exactly one issue is labelled `wayfinder:map`. Its children carry
  `wayfinder:grilling` (a decision), `wayfinder:research` (an investigation),
  `wayfinder:prototype` (a throwaway decision aid) or `wayfinder:task` (a build
  slice). Nothing else uses these labels.
- **The map is an index, not a store.** Its body sections, in order: `## Destination`,
  `## Notes`, `## Decisions so far`, `## Not yet specified`, `## Out of scope`. Open
  tickets are deliberately *not* listed — they are open child issues, found by query.
  The index holds one line per closed ticket, gist first, with the link inside the
  ticket's name: `- [<name>](<url>) — <one-line gist>`. A decision lives in exactly
  one place: its ticket.
- **Children are native sub-issues.** A ticket is created as a sub-issue of the map
  and its body opens `Part of wayfinder map #NNN.`
  (`gh api repos/<owner>/<repo>/issues/<map>/sub_issues` lists the children).
- **Blocking is body text, not the dependencies API.** Native dependencies are unused:
  a ticket that cannot start yet carries `Blocked by: <name> #id, …` on its second
  line, while its `dependencies/blocked_by` and `issue_dependencies_summary` stay
  empty — verified on a currently blocked ticket. **Frontier** = the map's open
  children whose every named blocker is closed:
  `gh issue list --state open --json number,title,labels`, then
  `gh issue view <n> --json body` and check each named blocker's state.
- **The assignee is the claim.** `gh issue edit <n> --add-assignee <login>` before any
  work, because unblocked tickets may be running in parallel sessions.
- **Resolution.** One resolution comment on the ticket carrying the answer in full,
  then close, then append the one-line gist to the map's `## Decisions so far`.
  Graduate the fog the answer made specifiable out of `## Not yet specified`; rule
  beyond-destination work into `## Out of scope` (one line: gist, warrant, link)
  rather than resolving it.
- **Refer by name.** In narration and in the index, a ticket is its title with the
  link inside the name — never a bare number or slug.
- **Artifacts are decision aids.** Research lands as `docs/research/<name>.md` on a
  throwaway `research/<name>` branch; prototypes as `prototype/*.html` with a
  THROWAWAY banner. Neither ships and the engine never reads them.



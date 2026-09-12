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


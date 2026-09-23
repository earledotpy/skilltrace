"""Forbidden-vocabulary translation (P3.1) — the one module no surface bypasses.

Normative source: the P3.1 accepted-in-principle vocabulary rules. The CLI
voice (command names, flags, ``[advisory]`` tags, ADR numbers, engine file
paths, raw record ids, engine-voice phrases) is banned from every page-surface
string: page copy, captured flashes, banner classes and titles.

Rule split:

* page composers never emit banned vocabulary (source truth);
* captured command stdout is *flash copy* — it flows through
  :func:`translate` before it reaches a flash (``views.writes``) or a page
  banner (``views._shared``); no write or read surface bypasses it;
* :func:`forbidden_matches` is the detector the tests and doc gates run to
  prove nothing leaked.

The table is written against the captured shapes from the P3.1 study: CLI
subcommand-name prefixes (``pass:``/``master:``/``evidence submit:``), CLI
flags, ``[advisory]`` tags, ``ADR NNNN`` numbers, engine relpaths, raw record
ids, and the engine-voice phrases.
"""

from __future__ import annotations

import re

# One banner kind map: the CLI's banner kinds (warning / error / advisory /
# ok) collapse onto the sublayer's semantic classes — the alias classes never
# reach a page (P5.4 alias collapse).
BANNER_KINDS: dict[str, str] = {
    "error": "err",
    "warning": "warn",
    "advisory": "attention",
    "ok": "success",
}

# CLI subcommand-name prefixes captured from the handlers, rewritten as the
# human act they are (P3.1 study prose). First words only — the body after
# the separator stays (it names the prerequisite truthfully).
_PREFIX_REWRITES: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(rf"^{re.escape(prefix)}\b\s*"), replacement)
    for prefix, replacement in (
        ("pass: FAILED", "Marked as passed is refused"),
        ("master: FAILED", "Marked as mastered is refused"),
        ("start: FAILED", "Starting this session is refused"),
        ("work: FAILED", "Recording this work session is refused"),
        ("work: REFUSED", "Recording this work session is refused"),
        ("work: refused", "Recording this work session is refused"),
        ("session close: FAILED", "Closing this session is refused"),
        ("blocker create: FAILED", "Recording the blocker is refused"),
        ("blocker resolve: FAILED", "Clearing the blocker is refused"),
        ("remediation create: FAILED", "Recording remediation is refused"),
        ("remediation complete: FAILED", "Completing remediation is refused"),
        ("review schedule: FAILED", "Scheduling the review is refused"),
        ("review complete: FAILED", "Completing the review is refused"),
        ("review cancel: FAILED", "Cancelling the review is refused"),
        ("export markdown: FAILED", "Exporting is refused"),
        ("export sqlite: FAILED", "Exporting is refused"),
        ("export html: FAILED", "Exporting is refused"),
        ("evidence submit: FAILED", "Recording evidence is refused"),
        ("evidence submit: refused", "Recording evidence is refused"),
        ("attempt record: FAILED", "Recording the practice attempt is refused"),
        ("attempt record: refused", "Recording the practice attempt is refused"),
        ("sync: FAILED", "Syncing is refused"),
        # success lines drop the CLI subcommand prefix (the celebration text
        # already names the act); engine ids on these lines are rewritten by
        # the id rules below.
        ("pass: refused", "Refused"),
        ("master: refused", "Refused"),
        ("evidence submit: wrote", "Evidence recorded"),
        ("attempt record: wrote", "Practice attempt recorded"),
        ("export markdown: wrote", "Export written"),
        ("export sqlite: wrote", "Export written"),
        ("export html: wrote", "Export written"),
        ("check-resources: FAILED", "The resource check is refused"),
        ("check-resources: BROKEN", "The resource check found a problem"),
        ("check-automation:", "The automated check"),
    )
)

# Gate/writer refusal shapes that carry the CLI verb inside the body (e.g.
# ``master blocked: node x is locked`` flowing through ``pass: FAILED — ...``),
# the engine-voice phrase, and engine relpaths on success lines (the page
# composers omit the path field; the flash carries none).
_PHRASES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bmaster blocked:"), "Marked as mastered is refused:"),
    (re.compile(r"\bpass blocked:"), "Marked as passed is refused:"),
    (re.compile(r"\bstart blocked:"), "Starting is refused:"),
    (re.compile(r"\bwork blocked:"), "Recording the work session is refused:"),
    (re.compile(r"\bsession close blocked:"), "Closing is refused:"),
    (re.compile(r"\bblocker create blocked:"), "Recording the blocker is refused:"),
    (re.compile(r"\bblocker resolve blocked:"), "Clearing the blocker is refused:"),
    (re.compile(r"\bevidence submit blocked:"), "Recording evidence is refused:"),
    (re.compile(r"\battempt record blocked:"), "Recording the attempt is refused:"),
    (re.compile(r"\breview schedule blocked:"), "Scheduling is refused:"),
    (re.compile(r"\bexport blocked:"), "Exporting is refused:"),
    (re.compile(r"\bthe domain refuses\b"), "it's refused"),
    (re.compile(r"\bThe domain refuses\b"), "It's refused"),
)

_ADVISORY_TAG = re.compile(r"^\[advisory\]\s*")
_ADVISORY_INLINE = re.compile(r"\[advisory\]\s*")
_FLAG = re.compile(r"(?<![\w`-])(--[a-z][a-z-]*)(?![\w-])")
_ADR_PAREN = re.compile(
    r"\s*\((?:ADR|accepted-in-principle)\s*[- ]?\s*\d{4}\)", re.IGNORECASE
)
_ADR_BARE = re.compile(
    r"\b(?:ADR|accepted-in-principle)\s*[- ]?\s*\d{4}:?\s*", re.IGNORECASE
)
_BACKTICK_CMD = re.compile(r"`skilltrace\s+[a-z][a-z -]*`(?![\w-])")
_BACKTICK_WORK = re.compile(r"`\s*work\s+\S+[^`]*`")
_EXIT_CODE = re.compile(r"\s*\(exit code \d+\)", re.IGNORECASE)
_RAW_ID = re.compile(
    r"(?<![\w./-])"  # not mid-token, not a path segment
    r"(?:spec|rec|work|ses|review|blocker|remediation|attempt|resource|"
    r"evidence|session)"
    r"[.\-][A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*"
    r"(?![\w-])"
)
_RELPATH = re.compile(r"\s+\S*/\S*\.(?:md|html|db|sqlite)\b")


def translate(text: str) -> str:
    """Apply the P3.1 rules to one string (banner-safe)."""
    if not text:
        return text
    out = text
    out = _ADVISORY_TAG.sub("", out)
    for pattern, replacement in _PREFIX_REWRITES:
        # the rewrite consumes the separator whitespace, so the human copy
        # carries the trailing space; the final strip cleans line ends.
        out = pattern.sub(replacement + " ", out)
    for pattern, replacement in _PHRASES:
        out = pattern.sub(replacement, out)
    out = _BACKTICK_WORK.sub("`work`", out)
    out = _BACKTICK_CMD.sub("the matching command", out)
    out = _FLAG.sub("", out)
    out = _ADR_PAREN.sub("", out)
    out = _ADR_BARE.sub("", out)
    out = _EXIT_CODE.sub("", out)
    out = _ADVISORY_INLINE.sub("", out)
    out = _RELPATH.sub("", out)
    out = _RAW_ID.sub("your record", out)
    # collapse the whitespace the drops left behind; trim; tidy punctuation.
    out = re.sub(r"  +", " ", out)
    out = re.sub(r"\s+([.,;:!?—-])", r"\1", out)
    out = re.sub(r"\( +", "(", out)
    out = re.sub(r"\s+'", " '", out)
    return out.strip()


def translate_lines(lines: list[str]) -> list[str]:
    """Apply :func:`translate` to each line of captured stdout."""
    return [translate(line) for line in lines]


_KIND_PREFIX = re.compile(r"^\[(error|warning|advisory)\]\s*")


def banners(lines: list[str], *, default_class: str = "") -> list[tuple[str, str]]:
    """Turn captured stdout into (kind, text) flash tuples, P3.1-clean.

    The CLI's banner kinds map onto the sublayer's semantic classes via
    :data:`BANNER_KINDS` (the alias classes never reach a page); plain lines
    keep ``default_class`` (the success flash's class). Banner-safe: every
    text goes through :func:`translate`.
    """
    out: list[tuple[str, str]] = []
    for line in lines:
        match = _KIND_PREFIX.match(line)
        if match:
            kind = BANNER_KINDS.get(match.group(1), "warn")
            text = translate(line[match.end():])
        else:
            kind = default_class or ""
            text = translate(line)
        if text:
            out.append((kind, text))
    return out


# The banned-vocabulary detector: the grep-able face of the P3.1 rules. Tests
# and doc gates run this against every page-surface string and fail on any
# match — the translation seam's contract is provable, not aspirational.
_BANNED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (label, re.compile(pattern, re.IGNORECASE))
    for label, pattern in (
        ("cli flag", r"(?<![\w`-])--[a-z][a-z-]*(?![\w-])"),
        ("cli command name", r"\bskilltrace\b"),
        ("cli subcommand prefix", r"^\s*(?:pass|master|evidence submit|blocker create|"
         r"blocker resolve|remediation create|remediation complete|review schedule|"
         r"review complete|review cancel|attempt record|export markdown|"
         r"export sqlite|export html|check-resources|session close|work|"
         r"start|sync):\s"),
        ("advisory tag", r"\[advisory\]"),
        ("warning tag", r"\[(?:error|warning)\]"),
        ("ADR number", r"\bADR\s+\d{4}\b"),
        ("engine relpath", r"(?<![\w.-])\S*/\S*\.(?:md|html|db|sqlite)\b"),
        ("engine-voice phrase", r"\bthe domain refuses\b"),
        ("cli help voice", r"\bthe CLI\b"),
    )
)


def forbidden_matches(text: str) -> list[str]:
    """The banned-vocabulary labels found in one string (empty = clean)."""
    if not text:
        return []
    return [label for label, pattern in _BANNED_PATTERNS if pattern.search(text)]


def forbidden_in_lines(lines: list[str]) -> list[str]:
    """The banned-vocabulary labels found across captured lines."""
    found: list[str] = []
    for line in lines:
        for label in forbidden_matches(line):
            if label not in found:
                found.append(label)
    return found


# --- The Richer Card translation seam (v2.4 §E) ---------------------------------
#
# Derivations produce ``MentorCard`` parts (the engine seam shared with the
# CLI); page bodies render ``interface.cards.Card`` objects through
# ``interface.render``. This translator is the one door between them: typed
# parts map onto the Richer Card's first-class fields, banner/appendix cards
# ride the banner channel, and a content card with no next-action fact gets
# **no affordance** (P4.1) — it is never re-derived from prose.


_DISPLAY_TO_STATE: dict[str, str] = {
    "locked": "locked",
    "available": "available",
    "active": "active",
    "passed": "passed",
    "mastered": "mastered",
    "ready to start": "available",
    "in progress": "active",
}


def _titlefy(text: str, titles: dict[str, str]) -> str:
    """Raw node ids in engine copy → the human title (P3.2 titles-not-ids)."""
    for node_id in sorted(titles, key=len, reverse=True):
        if node_id and node_id in text:
            text = text.replace(node_id, titles[node_id])
    return text


def rich_cards(
    model_cards,
    *,
    titles: dict[str, str] | None = None,
    default_state: str | None = None,
) -> tuple[list, list[tuple[str, str]]]:
    """Derived ``MentorCard`` lists → ``(cards, banner_tuples)``.

    Content cards carrying the Richer Card's minimum facts translate to
    :class:`interface.cards.Card` objects; banner/appendix cards (and any
    content card missing the minimum — e.g. the empty state) ride the
    banner channel with P3.1-cleaned, titlefied text.
    """
    from ...mentor.cards import Banner, Kicker, NextAction, Para, Pill, Sub, Title
    from .cards import Affordance, Card

    titles = titles or {}
    cards: list = []
    banner_tuples: list[tuple[str, str]] = []
    for model_card in model_cards:
        parts = model_card.parts
        if model_card.kind is not None or (
            len(parts) == 1 and isinstance(parts[0], Banner)
        ):
            kind = model_card.kind or parts[0].kind  # type: ignore[union-attr]
            text = " ".join(_part_text(p) for p in parts).strip()
            banner_tuples.append((kind, translate(_titlefy(text, titles))))
            continue
        card = _rich_content_card(parts, titles, default_state)
        if card is None:
            text = " ".join(_part_text(p) for p in parts).strip()
            banner_tuples.append(("advisory", translate(_titlefy(text, titles))))
        else:
            cards.append(card)
    return cards, banner_tuples


def _part_text(part) -> str:
    from ...mentor.cards import NextAction

    if isinstance(part, NextAction):
        return part.command or ""
    return getattr(part, "text", getattr(part, "label", ""))


def _rich_content_card(parts, titles: dict[str, str], default_state: str | None):
    """One content ``MentorCard`` → a Richer ``Card`` (or ``None``)."""
    from ...mentor.cards import Kicker, Label, NextAction, Para, Pill, Sub, Title
    from ...mentor.prose import NodeState, state_phrase
    from .cards import Affordance, Card

    state: str | None = None
    title: str | None = None
    why: str | None = None
    kicker: str | None = None
    affordance = None
    node_id: str | None = None
    resources: list[str] = []
    disclosure: list[str] = []
    section: str | None = None  # the Label currently being read

    for part in parts:
        if isinstance(part, Pill):
            state = _DISPLAY_TO_STATE.get(part.label.strip().lower())
            continue
        if isinstance(part, Title):
            title = part.text
            continue
        if isinstance(part, Kicker):
            if part.text.strip().upper() == "DO THIS NEXT":
                continue  # the action's chrome — the affordance replaces it
            if kicker is None:
                kicker = part.text
            continue
        if isinstance(part, NextAction):
            affordance = Affordance.from_intent(
                part.intent, binding=part, title=title
            )
            node_id = part.node_id
            continue
        if isinstance(part, (Label,)):
            section = part.text.strip().lower()
            if section.startswith("where to learn"):
                section = "resources"
            elif section.startswith("how to proceed"):
                section = "proceed"
            else:
                section = "other"
            continue
        text = getattr(part, "text", "")
        if not text.strip():
            continue
        if section == "resources":
            resources.append(text)
        elif section == "proceed":
            disclosure.append(text)
        elif why is None and isinstance(part, (Sub, Para)):
            why = text
        else:
            disclosure.append(text)

    if not title or affordance is None or state is None:
        return None  # not a Richer Card — banner channel (P4.1: no derived facts)

    if why is None:
        why = state_phrase(NodeState(state))
    if not resources:
        resources = ["No resources are registered for this skill yet."]
    return Card(
        state=state,
        title=title,
        why=why,
        resources=resources,
        affordances=(affordance,),
        disclosure=" ".join(disclosure) or None,
        kicker=kicker,
        node_id=node_id,
    )

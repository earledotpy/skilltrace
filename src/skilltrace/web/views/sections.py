"""The structured section data the views render (ADR 0006 escalation 1).

ADR 0006 sanctions one escalation: when the mechanical ``render.py``
transforms prove crusty, ``render.py`` becomes **structured section data**
consumed by both surfaces — never a parallel hand-declared vocabulary,
which would recreate the drift ADR 0002 cut. This module is that
structure, and its home is ADR 0009's ``views/`` package.

A page is a list of :class:`Section` values. A section has a title, an
optional meta line and a list of :class:`Block` values. A block is one of
the page's facts: a block of label/value rows, a data table, one of the
five named non-success states, or content that is already markup.

Why the vocabulary lives here and not in the interface sublayer: the
interface sublayer owns the **Card** vocabulary — the engine's facts and
their affordances — and a section is not a card. A section is a page's
frame: it groups facts under a heading and carries no state of its own.
Keeping the two apart is what stops a page frame from acquiring a
canonical state word it has no business claiming.

The renderer here is the only place that turns a section into markup, so
the same data can serve another surface — a plain-text export, a
different theme — without a second vocabulary of its own.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._shared import _esc, _table

#: The five non-success states the page contracts name (SC-00a). A page
#: never invents a sixth: a state it cannot name is a different fact.
EMPTY = "empty"
LIMITED = "limited"
REFUSAL = "refusal"
FAILURE = "failure"
RECOVERY = "recovery"

STATES = (EMPTY, LIMITED, REFUSAL, FAILURE, RECOVERY)


@dataclass(frozen=True)
class Rows:
    """A block of label/value fact rows.

    ``separated`` puts each row on its own line, for the pages whose
    rows are read one at a time; otherwise the rows run together, which
    is how a compact fact block reads.
    """

    pairs: tuple[tuple[str, str], ...]
    separated: bool = False

    def render(self) -> str:
        """The rows as markup — the values are already markup."""
        rows = [
            '<div class="row">'
            f'<span class="row-label">{_esc(label)}</span>'
            f'<span class="row-value">{value}</span>'
            "</div>"
            for label, value in self.pairs
        ]
        if self.separated:
            body = "\n".join(rows) + "\n"
        else:
            body = "".join(rows)
        return f'<div class="rows">\n{body}</div>\n'


@dataclass(frozen=True)
class Table:
    """A data table — a caption and column headers, then the rows."""

    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    caption: str = ""

    def render(self) -> str:
        """The table as markup."""
        return _table(list(self.headers), [list(row) for row in self.rows])


@dataclass(frozen=True)
class State:
    """One of the five named non-success states.

    ``kind`` is one of :data:`STATES`. The title and body carry the
    words; the kind carries only the register, so the meaning never
    rests on the colour.
    """

    kind: str
    title: str
    body: str

    def render(self) -> str:
        """The state as markup."""
        return (
            f'<div class="state state-{_esc(self.kind)}">\n'
            f'<p class="state-title">{_esc(self.title)}</p>\n'
            f'<p class="state-body">{_esc(self.body)}</p>\n'
            "</div>\n"
        )


@dataclass(frozen=True)
class Markup:
    """Content that is already markup.

    The escape hatch: a form, a disclosure or a chart is markup the page
    composed, and re-modelling it here would only move it.
    """

    html: str

    def render(self) -> str:
        """The markup, unchanged."""
        return self.html


#: The three frames a section may carry.
#:
#: ``HEAD`` groups the heading and the meta line in the head block. ``BARE``
#: carries the heading alone — a section whose blocks already say what they
#: are does not repeat it. ``INLINE`` carries the heading and the meta line
#: as siblings, for the sections that predate the head block.
HEAD = "head"
BARE = "bare"
INLINE = "inline"
NONE = "none"


@dataclass(frozen=True)
class Section:
    """One page section: a heading, a meta line and its blocks.

    ``frame`` chooses how the heading and the meta line are carried; the
    blocks are the same either way.
    """

    title: str
    meta: str = ""
    blocks: tuple[object, ...] = field(default_factory=tuple)
    frame: str = HEAD
    meta_markup: bool = False
    anchor: str = ""

    def render(self) -> str:
        """The section as markup."""
        inner = "".join(block.render() for block in self.blocks)
        anchor = f' id="{_esc(self.anchor)}"' if self.anchor else ""
        title = f'<h2 class="section-title">{_esc(self.title)}</h2>\n'
        # The meta line is content by default and is escaped. A page that
        # composes the line as markup says so, and is then responsible for
        # its own escaping — the same rule the blocks follow.
        meta_line = (
            f'<p class="section-meta">{self.meta}</p>\n'
            if self.meta_markup
            else f'<p class="section-meta">{_esc(self.meta)}</p>\n'
        )
        if self.frame == NONE:
            head = ""
        elif self.frame == HEAD:
            head = (
                '<div class="section-head">\n'
                + title
                + meta_line
                + "</div>\n"
            )
        elif self.frame == INLINE:
            head = title + meta_line
        else:
            head = title
        # The last block carries its own trailing whitespace: a section
        # does not add a newline the caller did not ask for.
        return (
            f'<section class="section"{anchor}>\n'
            + head
            + inner
            + "</section>\n"
        )


def render(sections: list[Section] | tuple[Section, ...]) -> str:
    """The sections as page markup."""
    return "".join(section.render() for section in sections)


def section(
    title: str,
    meta: str,
    inner: str,
    *,
    frame: str = HEAD,
    meta_markup: bool = False,
    anchor: str = "",
) -> str:
    """One section, from its heading and its already-rendered blocks.

    The shorthand for a page that assembles its own blocks: the frame
    comes from here, so no page hand-writes the section markup.
    """
    return Section(
        title,
        meta,
        (Markup(inner),),
        frame=frame,
        meta_markup=meta_markup,
        anchor=anchor,
    ).render()

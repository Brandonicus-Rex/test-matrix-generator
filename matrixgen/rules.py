"""A small, safe language for catalog rules (constraints).

Rules are written as text in the catalog, for example::

    device == 'iot' -> voicemail == 'off'
    plan in ['basic', 'plus'] and not device == 'tablet'

Supported syntax, from lowest to highest precedence:

    a -> b              "if a then b" (right-associative)
    a or b
    a and b
    not a
    (a)
    name == value       name != value
    name in [v1, v2]    name not in [v1, v2]

Values can be quoted ('iot') or bare words (iot). Rules are parsed into a
tiny syntax tree and evaluated by this module, never with Python's eval(),
so a catalog file can't run arbitrary code.

Evaluation is three-valued so rules can be checked against *partial*
assignments while a test is being built: True, False, or None (unknown,
because a parameter it depends on hasn't been chosen yet).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Sequence

KEYWORDS = {"and", "or", "not", "in"}

_TOKEN_RE = re.compile(
    r"""\s*(?:
        (?P<arrow>->)
      | (?P<op>==|!=)
      | (?P<lpar>\() | (?P<rpar>\))
      | (?P<lbr>\[)  | (?P<rbr>\])
      | (?P<comma>,)
      | (?P<str>'[^']*'|"[^"]*")
      | (?P<word>[A-Za-z0-9_.]+(?:-[A-Za-z0-9_.]+)*)
    )""",
    re.VERBOSE,
)


class RuleError(ValueError):
    """Raised for a rule that can't be parsed or refers to unknown names/values."""


# Syntax tree nodes are plain tuples:
#   ("cmp", param, op, (values...))   op is "==", "!=", "in" or "not in"
#   ("not", node)  ("and", [nodes])  ("or", [nodes])  ("implies", left, right)


@dataclass(frozen=True)
class Rule:
    """A parsed rule: its source text, syntax tree and the parameters it uses."""

    text: str
    tree: tuple
    params: frozenset[str]

    def evaluate(self, assignment: Mapping[str, str]) -> bool | None:
        """True/False, or None if a parameter the answer depends on is unset."""
        return _eval(self.tree, assignment)


# ---- Tokenizing and parsing ----------------------------------------------

def _tokenize(text: str) -> list[tuple[str, str]]:
    tokens, pos = [], 0
    text = text.rstrip()
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if not m or m.end() == pos:
            raise RuleError(f"unexpected character at position {pos} in rule: {text!r}")
        kind = m.lastgroup
        tokens.append((kind, m.group(kind)))
        pos = m.end()
    return tokens


class _Parser:
    def __init__(self, text: str):
        self.text = text
        self.tokens = _tokenize(text)
        self.pos = 0

    # helpers
    def _peek(self, offset: int = 0) -> tuple[str, str] | None:
        i = self.pos + offset
        return self.tokens[i] if i < len(self.tokens) else None

    def _is_word(self, word: str, offset: int = 0) -> bool:
        tok = self._peek(offset)
        return tok is not None and tok[0] == "word" and tok[1] == word

    def _take(self, kind: str) -> str:
        tok = self._peek()
        if tok is None or tok[0] != kind:
            found = "end of rule" if tok is None else repr(tok[1])
            raise RuleError(f"expected {kind} but found {found} in rule: {self.text!r}")
        self.pos += 1
        return tok[1]

    # grammar
    def parse(self) -> tuple:
        if not self.tokens:
            raise RuleError("rule is empty")
        tree = self._implies()
        if self._peek() is not None:
            raise RuleError(f"unexpected {self._peek()[1]!r} in rule: {self.text!r}")
        return tree

    def _implies(self) -> tuple:
        left = self._or()
        if self._peek() and self._peek()[0] == "arrow":
            self.pos += 1
            return ("implies", left, self._implies())
        return left

    def _or(self) -> tuple:
        items = [self._and()]
        while self._is_word("or"):
            self.pos += 1
            items.append(self._and())
        return items[0] if len(items) == 1 else ("or", items)

    def _and(self) -> tuple:
        items = [self._not()]
        while self._is_word("and"):
            self.pos += 1
            items.append(self._not())
        return items[0] if len(items) == 1 else ("and", items)

    def _not(self) -> tuple:
        if self._is_word("not"):
            self.pos += 1
            return ("not", self._not())
        return self._atom()

    def _atom(self) -> tuple:
        tok = self._peek()
        if tok and tok[0] == "lpar":
            self.pos += 1
            node = self._implies()
            self._take("rpar")
            return node
        name = self._take("word")
        if name in KEYWORDS:
            raise RuleError(f"expected a parameter name but found {name!r} in rule: {self.text!r}")
        tok = self._peek()
        if tok and tok[0] == "op":
            self.pos += 1
            return ("cmp", name, tok[1], (self._value(),))
        if self._is_word("in"):
            self.pos += 1
            return ("cmp", name, "in", self._list())
        if self._is_word("not") and self._is_word("in", 1):
            self.pos += 2
            return ("cmp", name, "not in", self._list())
        raise RuleError(f"expected ==, !=, in or not in after {name!r} in rule: {self.text!r}")

    def _value(self) -> str:
        tok = self._peek()
        if tok and tok[0] == "str":
            self.pos += 1
            return tok[1][1:-1]
        return self._take("word")

    def _list(self) -> tuple[str, ...]:
        self._take("lbr")
        values = [self._value()]
        while self._peek() and self._peek()[0] == "comma":
            self.pos += 1
            values.append(self._value())
        self._take("rbr")
        return tuple(values)


def _walk_cmps(tree: tuple):
    kind = tree[0]
    if kind == "cmp":
        yield tree
    elif kind == "not":
        yield from _walk_cmps(tree[1])
    elif kind in ("and", "or"):
        for child in tree[1]:
            yield from _walk_cmps(child)
    elif kind == "implies":
        yield from _walk_cmps(tree[1])
        yield from _walk_cmps(tree[2])


def compile_rule(text: str, domains: Mapping[str, Sequence[str]]) -> Rule:
    """Parse a rule and check every parameter and value it mentions exists.

    Checking values against the catalog catches typos such as
    ``device == 'iott'``, which would otherwise silently never match.

    Raises:
        RuleError: On a syntax error or an unknown parameter/value.
    """
    tree = _Parser(text).parse()
    params = set()
    for _, name, _, values in _walk_cmps(tree):
        if name not in domains:
            raise RuleError(f"unknown parameter {name!r} in rule: {text!r}")
        for value in values:
            if value not in domains[name]:
                raise RuleError(f"{value!r} is not a value of {name!r} in rule: {text!r}")
        params.add(name)
    return Rule(text=text, tree=tree, params=frozenset(params))


# ---- Three-valued evaluation ---------------------------------------------

def _eval(tree: tuple, a: Mapping[str, str]) -> bool | None:
    kind = tree[0]
    if kind == "cmp":
        _, name, op, values = tree
        if name not in a:
            return None
        hit = a[name] in values
        return hit if op in ("==", "in") else not hit
    if kind == "not":
        inner = _eval(tree[1], a)
        return None if inner is None else not inner
    if kind == "and":
        results = [_eval(child, a) for child in tree[1]]
        if False in results:
            return False
        return None if None in results else True
    if kind == "or":
        results = [_eval(child, a) for child in tree[1]]
        if True in results:
            return True
        return None if None in results else False
    if kind == "implies":
        # a -> b  is  (not a) or b
        left = _eval(tree[1], a)
        if left is False:
            return True
        right = _eval(tree[2], a)
        if right is True:
            return True
        if left is True and right is False:
            return False
        return None
    raise AssertionError(f"unknown node {kind!r}")  # pragma: no cover

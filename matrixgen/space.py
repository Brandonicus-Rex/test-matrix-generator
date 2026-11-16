"""The space of all combinations a catalog allows."""

from __future__ import annotations

from math import prod
from typing import Iterator, Mapping, Sequence

from matrixgen.rules import Rule

Assignment = dict[str, str]


class Space:
    """Parameters, their values and the rules that restrict combinations.

    The key operation is :meth:`can_complete`: given a partial assignment,
    is there at least one valid full combination that extends it? The
    generator uses it so it never paints itself into a corner, and the
    coverage code uses it to tell coverable pairs from impossible ones.
    """

    def __init__(self, parameters: Mapping[str, Sequence[str]], rules: Sequence[Rule] = ()):
        self.names: list[str] = list(parameters)
        self.values: dict[str, list[str]] = {n: list(v) for n, v in parameters.items()}
        self.rules = list(rules)
        self._complete_cache: dict[frozenset, bool] = {}

    @property
    def size(self) -> int:
        """Number of combinations before rules are applied."""
        return prod(len(v) for v in self.values.values())

    def consistent(self, partial: Mapping[str, str]) -> bool:
        """False if any rule is already definitely broken by ``partial``."""
        return all(rule.evaluate(partial) is not False for rule in self.rules)

    def is_valid(self, full: Mapping[str, str]) -> bool:
        """True if a complete assignment satisfies every rule."""
        return all(rule.evaluate(full) is True for rule in self.rules)

    def can_complete(self, partial: Mapping[str, str]) -> bool:
        """True if some valid full combination contains ``partial``.

        A depth-first search that stops at the first rule violation. Results
        are cached because the generator asks about the same partial
        assignments many times.
        """
        key = frozenset(partial.items())
        if key not in self._complete_cache:
            self._complete_cache[key] = self._search(dict(partial))
        return self._complete_cache[key]

    def _search(self, partial: Assignment) -> bool:
        if not self.consistent(partial):
            return False
        remaining = [n for n in self.names if n not in partial]
        if not remaining:
            return self.is_valid(partial)
        name = remaining[0]
        for value in self.values[name]:
            partial[name] = value
            if self.can_complete(partial):
                return True
        return False

    def iter_valid(self) -> Iterator[Assignment]:
        """Yield every valid combination, in parameter order."""
        yield from self._enumerate({}, 0)

    def _enumerate(self, partial: Assignment, index: int) -> Iterator[Assignment]:
        if not self.consistent(partial):
            return
        if index == len(self.names):
            if self.is_valid(partial):
                yield dict(partial)
            return
        name = self.names[index]
        for value in self.values[name]:
            partial[name] = value
            yield from self._enumerate(partial, index + 1)
            del partial[name]

    def count_valid(self) -> int:
        return sum(1 for _ in self.iter_valid())

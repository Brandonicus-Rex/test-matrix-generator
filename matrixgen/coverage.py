"""Measuring n-wise coverage: which value pairs (or triples) a test set covers."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, product
from typing import Iterable, Mapping, Sequence

from matrixgen.space import Space

# A tuple to cover, e.g. (("device", "iot"), ("plan", "basic")).
# Parameters always appear in catalog order so equal tuples compare equal.
Interaction = tuple[tuple[str, str], ...]


def all_interactions(space: Space, strength: int) -> Iterable[Interaction]:
    """Every combination of ``strength`` parameters and their values."""
    for names in combinations(space.names, strength):
        for values in product(*(space.values[n] for n in names)):
            yield tuple(zip(names, values))


def split_coverable(space: Space, strength: int) -> tuple[list[Interaction], list[Interaction]]:
    """Split interactions into (coverable, impossible).

    An interaction is coverable only if at least one valid full combination
    contains it. Impossible ones (e.g. ``device=iot`` with ``voicemail=on``
    when a rule forbids it) are reported, not counted as gaps.
    """
    coverable, impossible = [], []
    for inter in all_interactions(space, strength):
        (coverable if space.can_complete(dict(inter)) else impossible).append(inter)
    return coverable, impossible


def interactions_in(test: Mapping[str, str], names: Sequence[str], strength: int) -> set[Interaction]:
    """The interactions a single test covers."""
    return {tuple((n, test[n]) for n in combo) for combo in combinations(names, strength)}


@dataclass
class CoverageReport:
    strength: int
    required: int
    covered: int
    missing: list[Interaction] = field(default_factory=list)
    impossible: list[Interaction] = field(default_factory=list)

    @property
    def percent(self) -> float:
        return 100.0 if self.required == 0 else 100.0 * self.covered / self.required


def measure(tests: Sequence[Mapping[str, str]], space: Space, strength: int) -> CoverageReport:
    """Report how many coverable interactions ``tests`` cover."""
    coverable, impossible = split_coverable(space, strength)
    seen: set[Interaction] = set()
    for test in tests:
        seen |= interactions_in(test, space.names, strength)
    missing = [i for i in coverable if i not in seen]
    return CoverageReport(strength, len(coverable), len(coverable) - len(missing), missing, impossible)

"""Test generation strategies: exhaustive and n-wise (pairwise / 3-wise).

The n-wise generator is a greedy, one-test-at-a-time algorithm in the
spirit of AETG:

1. Work out every coverable interaction (pair, or triple for strength 3).
2. Build several candidate tests. Each starts from a random uncovered
   interaction, then fills the remaining parameters one by one, in random
   order, choosing the value that covers the most still-uncovered
   interactions. Values that would break a rule, or leave no valid way to
   finish the test, are never chosen.
3. Keep the candidate that covers the most, mark its interactions as
   covered, and repeat until nothing coverable is left.

Every test covers at least the interaction it started from, so the loop
always finishes. The result isn't guaranteed to be the smallest possible
set, but it's typically close and far smaller than exhaustive testing.
A seeded random generator makes the output repeatable.
"""

from __future__ import annotations

import random
from itertools import combinations

from matrixgen.coverage import Interaction, interactions_in, split_coverable
from matrixgen.space import Assignment, Space

DEFAULT_CANDIDATES = 30


def exhaustive(space: Space) -> list[Assignment]:
    """Every valid combination."""
    return list(space.iter_valid())


def nwise(space: Space, strength: int = 2, seed: int = 0,
          candidates: int = DEFAULT_CANDIDATES) -> list[Assignment]:
    """Generate tests covering every coverable ``strength``-way interaction.

    Raises:
        ValueError: If strength is below 2 or above the number of parameters.
    """
    if not 2 <= strength <= len(space.names):
        raise ValueError(f"strength must be between 2 and {len(space.names)}, got {strength}")
    rng = random.Random(seed)
    uncovered = set(split_coverable(space, strength)[0])
    tests: list[Assignment] = []

    while uncovered:
        # Sorted so the seeded choice doesn't depend on set ordering.
        pool = sorted(uncovered)
        best, best_gain = None, -1
        for _ in range(candidates):
            test = _build_candidate(space, strength, rng.choice(pool), uncovered, rng)
            gain = len(interactions_in(test, space.names, strength) & uncovered)
            if gain > best_gain:
                best, best_gain = test, gain
        tests.append(best)
        uncovered -= interactions_in(best, space.names, strength)
    return tests


def _build_candidate(space: Space, strength: int, start: Interaction,
                     uncovered: set[Interaction], rng: random.Random) -> Assignment:
    partial: Assignment = dict(start)
    order = [n for n in space.names if n not in partial]
    rng.shuffle(order)

    for name in order:
        scored = []
        for value in space.values[name]:
            trial = {**partial, name: value}
            if space.consistent(trial) and space.can_complete(trial):
                scored.append((_gain(space, strength, partial, name, value, uncovered), value))
        # Never empty: ``start`` is coverable and every step keeps the
        # partial assignment completable.
        top = max(gain for gain, _ in scored)
        partial[name] = rng.choice([value for gain, value in scored if gain == top])

    return {n: partial[n] for n in space.names}


def _gain(space: Space, strength: int, partial: Assignment, name: str, value: str,
          uncovered: set[Interaction]) -> int:
    """Uncovered interactions completed by setting ``name=value`` now."""
    gain = 0
    for others in combinations(partial, strength - 1):
        members = {**{o: partial[o] for o in others}, name: value}
        inter = tuple((n, members[n]) for n in space.names if n in members)
        gain += inter in uncovered
    return gain

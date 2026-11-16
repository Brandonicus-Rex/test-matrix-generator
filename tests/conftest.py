"""Shared fixtures, plus an independent coverage checker.

The checker deliberately doesn't use matrixgen.coverage or Space.can_complete:
it brute-forces every raw combination with itertools.product, so the
generator is verified against separate code, not against itself.
"""

from itertools import combinations, product
from pathlib import Path

import pytest

from matrixgen.catalog import load_catalog, parse_catalog

SAMPLE = Path(__file__).resolve().parent.parent / "samples" / "telecom_catalog.yaml"


@pytest.fixture
def catalog():
    return load_catalog(SAMPLE)


@pytest.fixture
def unconstrained():
    """Four 3-valued parameters, no rules. The best possible pairwise set is 9 tests."""
    return parse_catalog({"parameters": {p: ["1", "2", "3"] for p in "abcd"}})


def brute_force_valid(catalog):
    """Every valid full combination, found by plain enumeration."""
    names = list(catalog.parameters)
    valid = []
    for values in product(*catalog.parameters.values()):
        combo = dict(zip(names, values))
        if all(rule.evaluate(combo) is True for rule in catalog.rules):
            valid.append(combo)
    return valid


def brute_force_required(catalog, strength):
    """Interactions that appear in at least one valid combination."""
    names = list(catalog.parameters)
    required = set()
    for combo in brute_force_valid(catalog):
        for group in combinations(names, strength):
            required.add(tuple((n, combo[n]) for n in group))
    return required


def covered(tests, names, strength):
    return {tuple((n, t[n]) for n in group) for t in tests for group in combinations(names, strength)}

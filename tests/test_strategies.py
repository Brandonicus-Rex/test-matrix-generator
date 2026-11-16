"""Tests for exhaustive and n-wise generation, checked by brute force."""

import pytest

from conftest import brute_force_required, brute_force_valid, covered
from matrixgen.coverage import measure
from matrixgen.strategies import exhaustive, nwise


def as_set(tests):
    return {tuple(sorted(t.items())) for t in tests}


def test_exhaustive_matches_brute_force(catalog):
    expected = brute_force_valid(catalog)
    tests = exhaustive(catalog.space)
    assert as_set(tests) == as_set(expected)
    assert len(tests) == len(expected) == catalog.space.count_valid()


@pytest.mark.parametrize("strength", [2, 3])
@pytest.mark.parametrize("seed", [0, 1, 7, 42])
def test_nwise_covers_every_coverable_interaction(catalog, strength, seed):
    tests = nwise(catalog.space, strength, seed)
    required = brute_force_required(catalog, strength)
    assert required <= covered(tests, list(catalog.parameters), strength)


@pytest.mark.parametrize("strength", [2, 3])
def test_generated_tests_never_break_a_rule(catalog, strength):
    valid = as_set(brute_force_valid(catalog))
    for test in nwise(catalog.space, strength, seed=3):
        assert tuple(sorted(test.items())) in valid


def test_same_seed_same_output(catalog):
    assert nwise(catalog.space, 2, seed=5) == nwise(catalog.space, 2, seed=5)


def test_pairwise_is_much_smaller_than_exhaustive(catalog):
    pairwise, threewise = nwise(catalog.space, 2), nwise(catalog.space, 3)
    total = catalog.space.count_valid()
    assert len(pairwise) < len(threewise) < total
    assert len(pairwise) <= total // 4


def test_near_optimal_without_rules(unconstrained):
    # 4 parameters x 3 values: the theoretical minimum for pairwise is 9.
    tests = nwise(unconstrained.space, 2, seed=0)
    assert 9 <= len(tests) <= 11
    assert brute_force_required(unconstrained, 2) <= covered(tests, list("abcd"), 2)


def test_impossible_pairs_are_reported_not_counted(catalog):
    report = measure(nwise(catalog.space, 2), catalog.space, 2)
    impossible = {tuple(i) for i in report.impossible}
    assert (("device", "iot"), ("voicemail", "on")) in impossible
    assert (("plan", "basic"), ("hotspot", "on")) in impossible
    assert (("plan", "basic"), ("intl", "on")) in impossible
    assert report.percent == 100.0 and not report.missing


def test_coverage_report_spots_gaps(catalog):
    tests = nwise(catalog.space, 2)
    report = measure(tests[:-1], catalog.space, 2)
    assert report.missing and report.percent < 100


@pytest.mark.parametrize("strength", [1, 7])
def test_strength_out_of_range(catalog, strength):
    with pytest.raises(ValueError, match="strength"):
        nwise(catalog.space, strength)

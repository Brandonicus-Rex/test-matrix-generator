"""Tests for loading and validating catalogs."""

import pytest

from matrixgen.catalog import CatalogError, load_catalog, parse_catalog

BASE = {"parameters": {"plan": ["basic", "plus"], "voicemail": ["on", "off"]}}


def with_(**changes):
    return {**BASE, **changes}


def test_sample_catalog_loads(catalog):
    assert list(catalog.parameters) == ["plan", "device", "voicemail", "mms", "intl", "hotspot"]
    assert len(catalog.rules) == 5
    assert catalog.mapping["plan"].kind == "param"
    assert catalog.mapping["voicemail"].kind == "feature"
    assert catalog.mapping["device"].kind == "description"


def test_unquoted_on_off_stay_strings(tmp_path):
    # Plain YAML would turn these into True/False.
    path = tmp_path / "c.yaml"
    path.write_text("parameters:\n  a: [on, off]\n  b: [yes, no, true]\n")
    cat = load_catalog(path)
    assert cat.parameters == {"a": ["on", "off"], "b": ["yes", "no", "true"]}


def test_unmapped_parameters_default_to_description():
    assert parse_catalog(BASE).mapping["plan"].kind == "description"


@pytest.mark.parametrize("data,message", [
    ({}, "at least 2 parameters"),
    ({"parameters": {"a": ["1"]}}, "at least 2 parameters"),
    ({"parameters": {"a": [], "b": ["1"]}}, "non-empty list"),
    ({"parameters": {"a": ["1", "1"], "b": ["1"]}}, "duplicate"),
    (with_(constraints=["plan == gold"]), "is not a value"),
    (with_(mapping={"colour": {"to": "param"}}), "unknown parameter"),
    (with_(mapping={"plan": {"to": "header"}}), "must be one of"),
    (with_(mapping={"voicemail": {"to": "feature", "enabled": "yes"}}), "enabled value"),
    (with_(mapping={"voicemail": {"to": "feature", "name": "a,b"}}), "comma"),
    (with_(runner={"area_code": "12"}), "3 digits"),
])
def test_invalid_catalogs(data, message):
    with pytest.raises(CatalogError, match=message):
        parse_catalog(data)


def test_unreadable_file(tmp_path):
    with pytest.raises(CatalogError, match="could not read"):
        load_catalog(tmp_path / "missing.yaml")

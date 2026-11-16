"""Tests for output formats, including the contract with excel-regression-runner."""

import csv

from openpyxl import load_workbook

from matrixgen.coverage import measure
from matrixgen.strategies import nwise
from matrixgen.writers import (
    RUNNER_HEADERS, phone_for, render_report, runner_rows, write_csv, write_runner_workbook,
)

# The exact header row excel-regression-runner requires (runner/workbook.py).
# Kept as a separate literal on purpose: if either side changes, this fails.
RUNNER_CONTRACT = [
    "ID", "Description", "Action", "Phone", "Params", "Expected Status", "Expected Response",
    "Actual Status", "Actual Response", "Result", "Details",
]

TEST = {"plan": "plus", "device": "tablet", "voicemail": "off", "mms": "on", "intl": "on", "hotspot": "off"}


def test_headers_match_runner_contract():
    assert RUNNER_HEADERS == RUNNER_CONTRACT


def test_four_rows_per_test_with_expected_checks(catalog):
    setup, create, get, cleanup = runner_rows([TEST], catalog, "PW")
    assert [r[0] for r in (setup, create, get, cleanup)] == ["PW-01-S", "PW-01-A", "PW-01-B", "PW-01-C"]
    assert [r[2] for r in (setup, create, get, cleanup)] == ["close", "create", "get", "close"]
    assert setup[5] == "200,404,409" and setup[6] == ""
    assert create[4] == "plan=plus\nfeatures=mms,intl"
    assert create[5] == "201"
    assert create[6].splitlines() == [
        "plan=plus", "!features=voicemail", "features=mms", "features=intl", "!features=hotspot"]
    assert get[6].splitlines()[0] == "status=active" and get[6].splitlines()[1:] == create[6].splitlines()
    assert cleanup[5:] == ["200", "status=closed"]
    assert "device=tablet" in create[1]  # description-only parameter


def test_no_features_param_when_all_off(catalog):
    test = {**TEST, "mms": "off", "intl": "off"}
    assert runner_rows([test], catalog, "PW")[1][4] == "plan=plus"


def test_phone_numbers_are_fictional_and_rotate():
    assert phone_for(0, "201") == "2015550100"
    assert phone_for(99, "201") == "2015550199"
    assert phone_for(100, "201") == "2015550100"  # reused in rotation


def test_runner_workbook(catalog, tmp_path):
    tests = nwise(catalog.space, 2)
    path = tmp_path / "pw.xlsx"
    rows = write_runner_workbook(tests, catalog, path, "Pairwise", "PW")
    wb = load_workbook(path)
    assert wb.sheetnames == ["Pairwise", "Config"]
    ws = wb["Pairwise"]
    assert [c.value for c in ws[1]] == RUNNER_CONTRACT
    assert rows == 4 * len(tests) == ws.max_row - 1
    assert ws["F2"].value == "200,404,409" and ws["F2"].number_format == "@"


def test_csv(catalog, tmp_path):
    tests = nwise(catalog.space, 2)
    path = tmp_path / "t.csv"
    write_csv(tests, list(catalog.parameters), path)
    rows = list(csv.reader(path.open()))
    assert rows[0] == ["test", *catalog.parameters]
    assert len(rows) == len(tests) + 1


def test_report(catalog):
    tests = nwise(catalog.space, 2)
    md = render_report(catalog, "Pairwise", tests, measure(tests, catalog.space, 2), 63, 0)
    assert f"| **Tests generated** | **{len(tests)}** |" in md
    assert "100.0%" in md and "fewer tests" in md
    assert "device=iot, voicemail=on" in md  # listed as impossible

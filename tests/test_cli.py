"""End-to-end tests of the command line."""

from openpyxl import load_workbook

from conftest import SAMPLE
from matrixgen import cli


def test_pairwise_runner_workbook_and_report(tmp_path, capsys):
    out, report = tmp_path / "pw.xlsx", tmp_path / "pw.md"
    assert cli.main([str(SAMPLE), "-o", str(out), "--report", str(report)]) == 0
    printed = capsys.readouterr().out
    assert "Valid combinations (exhaustive): 63" in printed
    assert "100.0% of" in printed
    assert load_workbook(out).sheetnames == ["Pairwise", "Config"]
    assert report.read_text().startswith("# Test matrix: Fictional mobile catalog")


def test_threewise_and_exhaustive_csv(tmp_path):
    assert cli.main([str(SAMPLE), "--strength", "3", "--format", "csv", "-o", str(tmp_path / "t3.csv")]) == 0
    assert cli.main([str(SAMPLE), "--strategy", "exhaustive", "--format", "csv", "-o", str(tmp_path / "ex.csv")]) == 0
    assert len((tmp_path / "ex.csv").read_text().splitlines()) == 64  # header + 63


def test_md_format(tmp_path):
    out = tmp_path / "r.md"
    assert cli.main([str(SAMPLE), "--format", "md", "-o", str(out)]) == 0
    assert "## Tests" in out.read_text()


def test_bad_catalog_exit_code_2(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("parameters:\n  a: [1, 2]\n  b: [x]\nconstraints:\n  - a == 3\n")
    assert cli.main([str(bad)]) == 2
    assert "is not a value" in capsys.readouterr().err


def test_strength_larger_than_parameters(tmp_path):
    two = tmp_path / "two.yaml"
    two.write_text("parameters:\n  a: [1, 2]\n  b: [x, y]\n")
    assert cli.main([str(two), "--strength", "3", "-o", str(tmp_path / "x.xlsx")]) == 2

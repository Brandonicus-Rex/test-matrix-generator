"""Command-line entry point.

Examples::

    # Pairwise tests as an excel-regression-runner workbook (the default)
    python -m matrixgen samples/telecom_catalog.yaml -o pairwise_tests.xlsx

    # 3-wise coverage, with a Markdown coverage report alongside
    python -m matrixgen samples/telecom_catalog.yaml --strength 3 -o threewise.xlsx --report threewise.md

    # Every valid combination, as CSV
    python -m matrixgen samples/telecom_catalog.yaml --strategy exhaustive --format csv -o all.csv

Exit codes: 0 = success, 2 = bad input (catalog or arguments).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from matrixgen.catalog import CatalogError, load_catalog
from matrixgen.coverage import measure
from matrixgen.strategies import exhaustive, nwise
from matrixgen.writers import render_report, write_csv, write_runner_workbook

# Above this many raw combinations, exhaustive counting is skipped (it would
# be slow and the point of n-wise testing is not to enumerate everything).
MAX_EXHAUSTIVE = 200_000

PREFIXES = {("pairwise", 2): ("PW", "Pairwise"), ("pairwise", 3): ("T3", "3-wise"),
            ("exhaustive", None): ("EX", "Exhaustive")}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="matrixgen",
                                description="Generate exhaustive, pairwise or 3-wise test matrices from a catalog.")
    p.add_argument("catalog", type=Path, help="Catalog YAML file")
    p.add_argument("--strategy", choices=["pairwise", "exhaustive"], default="pairwise")
    p.add_argument("--strength", type=int, choices=[2, 3], default=2,
                   help="Pairwise strength: 2 = every pair (default), 3 = every triple")
    p.add_argument("--seed", type=int, default=0, help="Seed for repeatable pairwise output (default 0)")
    p.add_argument("--format", choices=["runner", "csv", "md"], default="runner",
                   help="runner = excel-regression-runner workbook (default), csv, or md report")
    p.add_argument("-o", "--output", type=Path, help="Output file (default depends on strategy and format)")
    p.add_argument("--report", type=Path, help="Also write a Markdown coverage report here")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        catalog = load_catalog(args.catalog)
    except CatalogError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    space = catalog.space
    if args.strategy == "exhaustive":
        if space.size > MAX_EXHAUSTIVE:
            print(f"error: {space.size} combinations is too many for exhaustive testing; use pairwise",
                  file=sys.stderr)
            return 2
        tests, seed, key = exhaustive(space), None, ("exhaustive", None)
    else:
        if args.strength > len(space.names):
            print(f"error: strength {args.strength} needs at least {args.strength} parameters", file=sys.stderr)
            return 2
        tests, seed, key = nwise(space, args.strength, args.seed), args.seed, ("pairwise", args.strength)

    prefix, label = PREFIXES[key]
    strength = args.strength if args.strategy == "pairwise" else 2
    coverage = measure(tests, space, strength)
    valid_total = space.count_valid() if space.size <= MAX_EXHAUSTIVE else None

    ext = {"runner": "xlsx", "csv": "csv", "md": "md"}[args.format]
    output = args.output or Path(f"{label.lower().replace('-', '')}_tests.{ext}")
    report = render_report(catalog, label, tests, coverage, valid_total, seed)
    try:
        if args.format == "runner":
            rows = write_runner_workbook(tests, catalog, output, label, prefix)
            written = f"runner workbook, {rows} rows"
        elif args.format == "csv":
            write_csv(tests, space.names, output)
            written = "CSV"
        else:
            output.write_text(report, encoding="utf-8")
            written = "Markdown report"
        if args.report:
            args.report.write_text(report, encoding="utf-8")
    except OSError as exc:
        print(f"error: could not write output: {exc}", file=sys.stderr)
        return 2

    unit = {2: "pairs", 3: "triples"}[strength]
    print(f"Catalog: {catalog.name} ({len(space.names)} parameters, {len(catalog.rules)} rules)")
    if valid_total is not None:
        print(f"Valid combinations (exhaustive): {valid_total}")
    print(f"{label}: {len(tests)} tests, {coverage.percent:.1f}% of {coverage.required} coverable {unit} covered"
          f" ({len(coverage.impossible)} impossible under the rules)")
    print(f"Wrote {output} ({written})" + (f" and {args.report}" if args.report else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

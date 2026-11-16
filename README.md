# test-matrix-generator

![CI](https://github.com/Brandonicus-Rex/test-matrix-generator/actions/workflows/ci.yml/badge.svg)

Combinatorial test design for product catalogs. Describe the plans, devices and
features you sell, plus the rules about what can't be combined, and the generator
produces the smallest practical set of test cases that covers every **pair** (or every
**triple**) of values. It writes them as a ready-to-run workbook for
[excel-regression-runner](https://github.com/Brandonicus-Rex/excel-regression-runner),
so test design flows straight into automated execution.

```
 catalog.yaml ──► matrixgen ──► pairwise_tests.xlsx ──► excel-regression-runner ──► PASS/FAIL
 (plans, features,   (pairwise or      (setup / create / read      (runs against the API)
  rules)              3-wise)            back / clean up rows)
```

## Why pairwise?

Most defects are triggered by a single setting or by an interaction between two.
Testing every combination quickly becomes impractical; testing every *pair* catches
most of those defects with a fraction of the tests. On the sample catalog:

| Strategy | Tests | Coverage |
|---|---|---|
| Exhaustive | 63 | every valid combination |
| **Pairwise** | **10** (84% fewer) | 100% of 76 coverable pairs |
| 3-wise | 22 (65% fewer) | 100% of 205 coverable triples |

## Highlights

- **Custom n-wise algorithm**: a greedy, AETG-style generator written from scratch
  (no pairwise library). Pairwise by default, `--strength 3` for 3-wise.
- **Rules (constraints)**: generated tests never break them, and value pairs they make
  impossible are reported separately instead of counted as coverage gaps.
- **Safe rule language**: rules are parsed by a small hand-written parser, never with
  `eval()`, and every parameter and value is checked against the catalog, so typos fail loudly.
- **Independent verification**: tests check coverage by brute force with separate code,
  for several seeds and both strengths.
- **Repeatable**: `--seed` gives identical output every run.
- **Integration with excel-regression-runner**: CI generates a workbook and runs it
  through the real runner against its mock API.

## Catalog format

```yaml
name: Fictional mobile catalog
parameters:
  plan:      [basic, plus, unlimited]
  device:    [phone, tablet, iot]
  voicemail: [on, off]
  mms:       [on, off]
  intl:      [on, off]
  hotspot:   [on, off]

constraints:
  - device == 'iot' -> voicemail == 'off'
  - plan == 'basic' -> hotspot == 'off'
  - intl == 'on' -> plan in ['plus', 'unlimited']

mapping:                          # how each parameter becomes a runner row
  plan:      {to: param}          # sent as plan=<value> and checked in the response
  voicemail: {to: feature}        # on: in the features list; off: must be absent
  device:    {to: description}    # not sent; shown in the Description column

runner:
  area_code: "201"                # phone numbers 201-555-01xx (fictional range)
```

Rule syntax: `==`, `!=`, `in [...]`, `not in [...]`, `and`, `or`, `not`,
parentheses, and `->` for "if … then". Values can be quoted or bare words.
Unquoted `on`/`off`/`yes`/`no` stay as text (plain YAML would turn them into booleans).

## Quick start

Requires Python 3.10 to 3.13.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt

python -m matrixgen samples/telecom_catalog.yaml -o pairwise_tests.xlsx --report pairwise_report.md
```

```
Catalog: Fictional mobile catalog (6 parameters, 5 rules)
Valid combinations (exhaustive): 63
Pairwise: 10 tests, 100.0% of 76 coverable pairs covered (5 impossible under the rules)
Wrote pairwise_tests.xlsx (runner workbook, 40 rows) and pairwise_report.md
```

More options:

```bash
python -m matrixgen samples/telecom_catalog.yaml --strength 3 -o threewise_tests.xlsx
python -m matrixgen samples/telecom_catalog.yaml --strategy exhaustive --format csv -o all.csv
python -m matrixgen samples/telecom_catalog.yaml --format md -o report.md --seed 7
```

Example outputs are in [samples/output](samples/output).

## Running the tests with excel-regression-runner

Each generated test becomes four rows, so every combination is self-contained and
rounds can be repeated:

| Row | Action | Expected |
|---|---|---|
| `PW-03-S` | close (setup) | `200,404,409`: clears anything left over |
| `PW-03-A` | create | `201`, `plan=plus`, `features=mms`, `!features=voicemail`, ... |
| `PW-03-B` | get | `200`, `status=active` and the same feature checks |
| `PW-03-C` | close (cleanup) | `200`, `status=closed` |

The Description column shows the full combination, so a failure tells you exactly which
combination broke.

```bash
# from your excel-regression-runner folder, with its mock API running
python -m runner.cli path/to/pairwise_tests.xlsx
```

The workbook also includes a Config sheet, so you can save it as `.xlsm` and use the
runner's Excel macro (double-click a test ID or click **Run selected**).

## How the generator works

1. List every coverable pair (or triple). A pair is coverable only if at least one valid
   full combination contains it, checked with a depth-first search that prunes as soon
   as a rule is broken.
2. Build candidate tests: start from a random uncovered pair, then fill each remaining
   parameter (in random order) with the value that completes the most uncovered pairs,
   skipping any value that would break a rule or leave no valid way to finish.
3. Keep the best of 30 candidates, mark its pairs covered, and repeat until done.

Rules are evaluated with three-valued logic (true / false / unknown), so they can be
checked while a test is only partly built.

## Tests

```bash
python -m pytest
```

66 tests cover the rule parser, catalog validation, coverage (verified by brute force),
determinism, output formats and the column contract with excel-regression-runner.

## Project layout

```
matrixgen/
  rules.py       safe rule parser and three-valued evaluator
  space.py       valid combinations and "can this partial test be completed?"
  coverage.py    pair/triple coverage measurement
  strategies.py  exhaustive and n-wise generation
  catalog.py     YAML loading and validation
  writers.py     runner workbook, CSV and Markdown report
  cli.py         command-line entry point
samples/         sample catalog and example outputs
tests/
```

## License

MIT

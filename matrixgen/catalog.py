"""Loading and validating a catalog file (YAML).

A catalog describes what can be combined and how each parameter maps to
an ``excel-regression-runner`` test row::

    name: Fictional mobile catalog
    parameters:
      plan:      [basic, plus, unlimited]
      device:    [phone, tablet, iot]
      voicemail: [on, off]
    constraints:
      - device == 'iot' -> voicemail == 'off'
    mapping:
      plan:      {to: param}        # sent as plan=basic and checked in the response
      voicemail: {to: feature}      # on -> in the features list, off -> must be absent
      device:    {to: description}  # shown in the Description column only
    runner:
      area_code: "201"              # phone numbers are <area>555-01xx (fictional)

Parameters not listed under ``mapping`` default to ``description``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from matrixgen.rules import Rule, RuleError, compile_rule
from matrixgen.space import Space

MAPPING_KINDS = {"param", "feature", "description"}


class CatalogError(ValueError):
    """Raised when a catalog file is missing data or inconsistent."""


@dataclass(frozen=True)
class Mapping:
    kind: str                 # "param", "feature" or "description"
    name: str                 # API parameter or feature name
    enabled: str = "on"       # for features: the value meaning "turned on"


@dataclass
class Catalog:
    name: str
    parameters: dict[str, list[str]]
    rules: list[Rule]
    mapping: dict[str, Mapping]
    area_code: str = "201"
    source: Path | None = None
    space: Space = field(init=False)

    def __post_init__(self) -> None:
        self.space = Space(self.parameters, self.rules)


class _Loader(yaml.SafeLoader):
    """YAML loader that keeps on/off/yes/no/true/false as plain strings.

    Standard YAML turns an unquoted ``on`` into True, which would make
    ``voicemail: [on, off]`` silently become ``[True, False]``.
    """


_Loader.yaml_implicit_resolvers = {
    key: [r for r in resolvers if r[0] != "tag:yaml.org,2002:bool"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_catalog(path: str | Path) -> Catalog:
    """Read and validate a catalog file.

    Raises:
        CatalogError: If the file is malformed or inconsistent.
    """
    path = Path(path)
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader)
    except (OSError, yaml.YAMLError) as exc:
        raise CatalogError(f"could not read {path}: {exc}") from None
    catalog = parse_catalog(data if isinstance(data, dict) else {})
    catalog.source = path
    return catalog


def parse_catalog(data: dict) -> Catalog:
    """Validate an already-loaded catalog dictionary."""
    params = data.get("parameters")
    if not isinstance(params, dict) or len(params) < 2:
        raise CatalogError("catalog needs a 'parameters' section with at least 2 parameters")
    parameters: dict[str, list[str]] = {}
    for name, values in params.items():
        if not isinstance(values, list) or not values:
            raise CatalogError(f"parameter {name!r} needs a non-empty list of values")
        values = [str(v) for v in values]
        if len(set(values)) != len(values):
            raise CatalogError(f"parameter {name!r} has duplicate values")
        parameters[str(name)] = values

    try:
        rules = [compile_rule(str(text), parameters) for text in data.get("constraints") or []]
    except RuleError as exc:
        raise CatalogError(str(exc)) from None

    mapping = {name: Mapping("description", name) for name in parameters}
    for name, spec in (data.get("mapping") or {}).items():
        if name not in parameters:
            raise CatalogError(f"mapping refers to unknown parameter {name!r}")
        spec = spec or {}
        kind = spec.get("to", "description")
        if kind not in MAPPING_KINDS:
            raise CatalogError(f"mapping for {name!r}: 'to' must be one of {sorted(MAPPING_KINDS)}")
        m = Mapping(kind, str(spec.get("name", name)), str(spec.get("enabled", "on")))
        if kind == "feature":
            if m.enabled not in parameters[name]:
                raise CatalogError(f"feature {name!r}: enabled value {m.enabled!r} is not one of its values")
            if "," in m.name:
                raise CatalogError(f"feature name {m.name!r} can't contain a comma")
        mapping[name] = m

    area = str((data.get("runner") or {}).get("area_code", "201"))
    if not (area.isdigit() and len(area) == 3):
        raise CatalogError("runner.area_code must be 3 digits")

    return Catalog(str(data.get("name", "Catalog")), parameters, rules, mapping, area)

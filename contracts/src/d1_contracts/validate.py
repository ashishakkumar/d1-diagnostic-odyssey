"""Parse the pipeline contract and check Phenopackets v2 messages with the library."""

from typing import Any

import phenopackets.schema.v2 as pps2
from google.protobuf.json_format import ParseDict, ParseError
from pydantic import BaseModel

from d1_contracts.canonical import canonical_json
from d1_contracts.generated import Pipeline, Report


class ContractError(ValueError):
    """The document is not this contract, or its case is not a Phenopacket v2."""


def _object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, BaseModel):
        dumped = value.model_dump(mode="json", by_alias=True, exclude_none=True)
        if isinstance(dumped, dict):
            return dumped
    raise ContractError("expected an object")


def _require_phenopacket(case: dict[str, Any]) -> None:
    try:
        packet = ParseDict(case, pps2.Phenopacket())
    except ParseError as exc:
        raise ContractError(str(exc)) from exc
    if not packet.meta_data.phenopacket_schema_version.startswith("2"):
        raise ContractError("case is not a Phenopacket schema v2 document")


def _require_variation(variation: dict[str, Any]) -> None:
    try:
        ParseDict(variation, pps2.VariationDescriptor())
    except ParseError as exc:
        raise ContractError(str(exc)) from exc


def _require_report_pair(model: Report) -> None:
    has_probability = model.probability is not None
    has_curve = model.reliability_curve is not None
    if has_probability != has_curve:
        raise ContractError("a probability is valid only together with a reliability curve")


def parse_report(data: dict[str, Any]) -> Report:
    model = Report.model_validate(data)
    _require_report_pair(model)
    return model


def parse_pipeline(data: dict[str, Any]) -> Pipeline:
    model = Pipeline.model_validate(data)
    _require_phenopacket(_object(model.case))
    for variant in model.lab_reported_variants:
        _require_variation(_object(variant.variation))
    if model.report is not None:
        _require_report_pair(model.report)
    return model


def dump_pipeline(model: Pipeline) -> str:
    return canonical_json(model.model_dump(mode="json", by_alias=True, exclude_none=True))

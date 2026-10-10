import json
import subprocess
from pathlib import Path

import phenopackets.schema.v2 as pps2
import pytest
from google.protobuf.json_format import MessageToDict, ParseDict

from canonical_oracle import body_hash, canonical_json
from d1_contracts import (
    ApprovalRequest,
    dump_pipeline,
    parse_pipeline,
)
from d1_contracts import (
    body_hash as package_body_hash,
)
from d1_contracts import (
    canonical_json as package_canonical_json,
)

ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "00000000-0000-4000-8000-000000000010"


def sample_case() -> dict:
    packet = pps2.Phenopacket(
        id="synthetic-case-1",
        subject=pps2.Individual(id="synthetic-subject-1", sex=pps2.MALE),
        phenotypic_features=[
            pps2.PhenotypicFeature(
                type=pps2.OntologyClass(id="HP:0001250", label="Seizure"),
            )
        ],
        meta_data=pps2.MetaData(
            created_by="synthetic-fixture",
            phenopacket_schema_version="2.0.0",
            resources=[
                pps2.Resource(
                    id="hp",
                    name="Human Phenotype Ontology",
                    namespace_prefix="HP",
                    version="test",
                    iri_prefix="http://purl.obolibrary.org/obo/HP_",
                )
            ],
        ),
    )
    return MessageToDict(packet)


def sample_variation() -> dict:
    descriptor = pps2.VariationDescriptor(
        id="synthetic-var-1",
        gene_context=pps2.GeneDescriptor(value_id="HGNC:3603", symbol="FBN1"),
        expressions=[pps2.Expression(syntax="hgvs.c", value="NM_000138.5:c.1A>G")],
    )
    return MessageToDict(descriptor)


def sample_pipeline() -> dict:
    return {
        "case": sample_case(),
        "hpo_term_drafts": [
            {
                "id": "00000000-0000-4000-8000-000000000001",
                "case_id": CASE_ID,
                "hpo_id": "HP:0001250",
                "label": "Seizure",
                "presence": "uncertain",
            }
        ],
        "accepted_terms": [
            {
                "id": "00000000-0000-4000-8000-000000000002",
                "case_id": CASE_ID,
                "draft_id": "00000000-0000-4000-8000-000000000001",
                "hpo_id": "HP:0001250",
                "label": "Seizure",
                "presence": "present",
                "approval_id": "00000000-0000-4000-8000-000000000020",
            }
        ],
        "lab_reported_variants": [
            {
                "id": "00000000-0000-4000-8000-000000000003",
                "case_id": CASE_ID,
                "gene_symbol": "FBN1",
                "lab_words": "the laboratory report's own words",
                "report_date": "2020-01-02",
                "variation": sample_variation(),
            }
        ],
        "evidence": [
            {
                "id": "00000000-0000-4000-8000-000000000004",
                "source": "ClinVar",
                "version": "2026-10-synthetic",
            }
        ],
        "change_events": [
            {
                "id": "00000000-0000-4000-8000-000000000005",
                "case_id": CASE_ID,
                "source": "ClinVar",
                "version": "2026-10-synthetic",
                "subject_key": "synthetic-accession",
            }
        ],
        "approvals": [
            {
                "id": "00000000-0000-4000-8000-000000000020",
                "draft_id": "00000000-0000-4000-8000-000000000001",
                "reviewer": "ashish",
                "decision": "approve",
                "body_hash": "ab" * 32,
                "decided_at": "2026-10-10T00:00:00Z",
            }
        ],
    }


def test_pipeline_round_trip_keeps_the_phenopacket() -> None:
    raw = sample_pipeline()
    model = parse_pipeline(raw)
    again = parse_pipeline(json.loads(dump_pipeline(model)))
    assert again == model
    packet = ParseDict(again.case.model_dump(mode="json", by_alias=True), pps2.Phenopacket())
    original = ParseDict(raw["case"], pps2.Phenopacket())
    assert packet == original
    assert packet.meta_data.phenopacket_schema_version.startswith("2")
    descriptor = ParseDict(
        again.lab_reported_variants[0].variation.model_dump(mode="json", by_alias=True),
        pps2.VariationDescriptor(),
    )
    assert descriptor.gene_context.symbol == "FBN1"


def test_pipeline_rejects_an_invented_case_field() -> None:
    raw = sample_pipeline()
    raw["case"]["notAField"] = 1
    with pytest.raises(Exception):
        parse_pipeline(raw)


def test_pipeline_rejects_a_top_level_diagnosis() -> None:
    raw = sample_pipeline()
    raw["diagnosis"] = "not a field on this contract"
    with pytest.raises(Exception):
        parse_pipeline(raw)


def test_case_must_be_phenopacket_schema_v2() -> None:
    raw = sample_pipeline()
    raw["case"]["metaData"]["phenopacketSchemaVersion"] = "1.0.0"
    with pytest.raises(Exception):
        parse_pipeline(raw)


def test_approval_request_has_no_reviewer() -> None:
    assert "reviewer" not in ApprovalRequest.model_fields
    ApprovalRequest.model_validate(
        {
            "draft_id": "00000000-0000-4000-8000-000000000001",
            "decision": "approve",
            "seen_hash": "ab" * 32,
        }
    )
    with pytest.raises(Exception):
        ApprovalRequest.model_validate(
            {
                "draft_id": "00000000-0000-4000-8000-000000000001",
                "decision": "approve",
                "seen_hash": "ab" * 32,
                "reviewer": "forged",
            }
        )


def test_lab_words_are_free_text() -> None:
    schema = json.loads((ROOT / "contracts" / "pipeline.schema.json").read_text())
    lab_words = schema["$defs"]["LabReportedVariant"]["properties"]["lab_words"]
    assert lab_words["type"] == "string"
    assert "enum" not in lab_words


def test_canonical_json_folds_nfc_and_sorts_keys() -> None:
    raw = {"b": 1, "a": "e\u0301"}
    assert package_canonical_json(raw) == canonical_json(raw) == '{"a":"é","b":1}'
    assert package_body_hash(raw) == body_hash(raw)


def test_typescript_round_trip(tmp_path: Path) -> None:
    raw = sample_pipeline()
    text = dump_pipeline(parse_pipeline(raw))
    fixture = tmp_path / "pipeline.json"
    fixture.write_text(text)
    script = ROOT / "contracts" / "ts" / "dist" / "roundtrip.js"
    completed = subprocess.run(
        ["node", str(script), str(fixture)],
        check=True,
        capture_output=True,
        text=True,
    )
    echoed = json.loads(completed.stdout)
    assert parse_pipeline(echoed) == parse_pipeline(raw)

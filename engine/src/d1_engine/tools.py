"""Shell out to Exomiser and LIRICAL. This file does not score variants."""

import csv
import json
import subprocess
from pathlib import Path

from d1_engine.gate import GateError


def _table(text: str) -> list[dict[str, str]]:
    kept: list[str] = []
    for line in text.splitlines():
        if not line or line.startswith("!") or line.startswith("##"):
            continue
        kept.append(line[1:] if line.startswith("#") else line)
    return list(csv.DictReader(kept, delimiter="\t"))


def parse_exomiser_genes(text: str, *, version: str) -> list[dict]:
    rows = []
    for row in _table(text):
        rows.append(
            {
                "kind": "gene",
                "label": row["GENE_SYMBOL"],
                "tool": "exomiser",
                "tool_version": version,
                "score": float(row["EXOMISER_GENE_COMBINED_SCORE"]),
                "score_name": "EXOMISER_GENE_COMBINED_SCORE",
            }
        )
    return rows


def parse_lirical(text: str, *, version: str) -> list[dict]:
    rows = []
    for row in _table(text):
        rows.append(
            {
                "kind": "disease",
                "label": row["diseaseName"],
                "tool": "lirical",
                "tool_version": version,
                "score": float(row["compositeLR"]),
                "score_name": "compositeLR",
            }
        )
    return rows


def exomiser_argv(*, jar: Path, analysis: Path, output: Path) -> list[str]:
    return [
        "java",
        "-jar",
        str(jar),
        "analyse",
        "--analysis",
        str(analysis),
        "--output-directory",
        str(output),
        "--output-format",
        "TSV_GENE",
    ]


def lirical_argv(
    *,
    jar: Path,
    phenopacket: Path,
    vcf: Path | None,
    output_prefix: Path,
    assembly: str,
    exomiser_dir: Path,
    hpo_ids: list[str] | None = None,
) -> list[str]:
    data_flag = "--exomiser-hg38-dir" if assembly == "hg38" else "--exomiser-hg19-dir"
    argv = [
        "java",
        "-jar",
        str(jar),
        "phenopacket",
        "--assembly",
        assembly,
        data_flag,
        str(exomiser_dir),
        "--phenopacket",
        str(phenopacket),
        "--output-format",
        "tsv",
        "-x",
        str(output_prefix),
    ]
    if vcf is not None:
        argv.extend(["--vcf", str(vcf)])
    # Accepted HPO terms are written into the phenopacket. hpo_ids is that list.
    if hpo_ids is not None:
        return argv
    return argv


def job_yaml(*, vcf: Path | None, hpo_ids: list[str], mode: str) -> str:
    """Preset names from the Exomiser analysis docs. Not a local score."""
    if mode == "phenotype":
        preset = "PHENOTYPE_ONLY"
    elif mode == "genotype" or mode == "both":
        preset = "EXOME"
    else:
        raise GateError(mode)
    lines = ["---", "proband: sample", f"preset: {preset}"]
    if mode != "genotype" and hpo_ids:
        quoted = ", ".join(f"'{term}'" for term in hpo_ids)
        lines.append(f"hpoIds: [{quoted}]")
    if mode != "phenotype" and vcf is not None:
        lines.append(f"vcf: {vcf}")
    lines.extend(
        [
            "outputOptions:",
            "  outputFormats: [TSV_GENE]",
            "  outputFileName: engine",
            "  numGenes: 0",
        ]
    )
    return "\n".join(lines) + "\n"


def execute(argv: list[str]) -> int:
    completed = subprocess.run(argv, check=False, capture_output=True, text=True)
    return completed.returncode


def phenopacket_json(*, hpo_ids: list[str], vcf: Path | None, mode: str) -> str:
    features = [{"type": {"id": term}} for term in hpo_ids] if mode != "genotype" else []
    packet: dict = {
        "id": "experimental-local",
        "subject": {"id": "experimental-local"},
        "phenotypicFeatures": features,
        "metaData": {
            "createdBy": "d1-engine",
            "phenopacketSchemaVersion": "2.0",
        },
    }
    if vcf is not None and mode != "phenotype":
        packet["htsFiles"] = [{"uri": str(vcf), "htsFormat": "VCF", "genomeAssembly": "hg38"}]
    return json.dumps(packet)

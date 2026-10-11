"""Public-fixture evaluation. A missing tool run does not invent a rank."""

from pathlib import Path

from fastapi.testclient import TestClient

from d1_engine.evalrun import evaluate, precision_recall
from d1_engine.gate import ACK_TEXT, BANNER
from d1_engine.http import create_app
from d1_engine.tools import exomiser_argv, lirical_argv
from d1_engine.vcf import spike, variants_from_phenopacket

ROOT = Path(__file__).resolve().parents[2]
BACKGROUND = (
    "##fileformat=VCFv4.2\n"
    "##source=synthetic-background-not-1000-genomes\n"
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
    "chr1\t1000\t.\tA\tG\t.\tPASS\t.\n"
)
PACKET = {
    "id": "synthetic-spike",
    "interpretations": [
        {
            "diagnosis": {
                "genomicInterpretations": [
                    {
                        "variantInterpretation": {
                            "variationDescriptor": {
                                "geneContext": {"symbol": "SYN1"},
                                "vcfRecord": {
                                    "genomeAssembly": "GRCh38",
                                    "chrom": "chr10",
                                    "pos": 12345,
                                    "ref": "C",
                                    "alt": "T",
                                },
                            }
                        }
                    }
                ]
            }
        }
    ],
}


def test_precision_recall_counts_a_planted_label() -> None:
    assert precision_recall(["SYN1", "DEC1"], "SYN1", 1) == (1.0, 1.0)
    assert precision_recall(["DEC1", "SYN1"], "SYN1", 1) == (0.0, 0.0)
    assert precision_recall(["DEC1", "SYN1"], "SYN1", 2) == (0.5, 1.0)


def test_a_missing_tool_does_not_invent_precision(tmp_path: Path) -> None:
    result = evaluate(jar=tmp_path / "missing.jar", tool_output=None)
    assert result["status"] == "not-run"
    assert result["ranks"] == []
    assert "precision" not in result
    assert "recall" not in result


def test_commands_invoke_the_pinned_jars_unchanged(tmp_path: Path) -> None:
    vcf = tmp_path / "panel.vcf"
    vcf.write_text(BACKGROUND, encoding="utf-8")
    exomiser = exomiser_argv(
        jar=Path("/opt/exomiser/exomiser-cli-15.1.0.jar"),
        analysis=tmp_path / "job.yml",
        output=tmp_path / "out",
    )
    assert exomiser[:3] == ["java", "-jar", "/opt/exomiser/exomiser-cli-15.1.0.jar"]
    assert "analyse" in exomiser
    assert "TSV_GENE" in exomiser
    both = lirical_argv(
        jar=Path("/opt/lirical/lirical-cli-2.4.1.jar"),
        phenopacket=tmp_path / "packet.json",
        vcf=vcf,
        output_prefix=tmp_path / "lirical",
        assembly="hg38",
        exomiser_dir=Path("/data/exomiser/2602_hg38"),
    )
    phenotype = lirical_argv(
        jar=Path("/opt/lirical/lirical-cli-2.4.1.jar"),
        phenopacket=tmp_path / "packet.json",
        vcf=None,
        output_prefix=tmp_path / "lirical-pheno",
        assembly="hg38",
        exomiser_dir=Path("/data/exomiser/2602_hg38"),
    )
    genotype = lirical_argv(
        jar=Path("/opt/lirical/lirical-cli-2.4.1.jar"),
        phenopacket=tmp_path / "packet.json",
        vcf=vcf,
        output_prefix=tmp_path / "lirical-geno",
        assembly="hg38",
        exomiser_dir=Path("/data/exomiser/2602_hg38"),
        hpo_ids=[],
    )
    assert "phenopacket" in both
    assert "--vcf" in both
    assert "--vcf" not in phenotype
    assert "--vcf" in genotype
    assert "2.4.1" in " ".join(both)


def test_spike_adds_a_packet_variant_and_a_decoy() -> None:
    variants = variants_from_phenopacket(PACKET)
    vcf = spike(BACKGROUND, variants, decoys=["DEC1"])
    assert "SYN1" in vcf
    assert "DEC1" in vcf
    assert "TRUTH" not in vcf
    assert "chr10\t12345" in vcf
    assert "synthetic-background-not-1000-genomes" in vcf
    assert len(variants) == 1
    assert variants[0].gene == "SYN1"


def test_a_packet_without_a_vcf_record_is_not_converted() -> None:
    packet = {"interpretations": [{"diagnosis": {"genomicInterpretations": []}}]}
    assert variants_from_phenopacket(packet) == []


def test_local_run_without_a_jar_does_not_rank(tmp_path: Path) -> None:
    vcf = tmp_path / "panel.vcf"
    vcf.write_text(BACKGROUND, encoding="utf-8")
    ack = tmp_path / "ACKNOWLEDGEMENT"
    ack.write_text(ACK_TEXT, encoding="utf-8")
    env = {"D1_TRACK": "experimental-local", "D1_BIND": "127.0.0.1", "D1_INPUT": str(tmp_path)}
    app = create_app(env, ack, "local")
    client = TestClient(app)
    response = client.post(
        "/run",
        json={"vcf": str(vcf), "hpo_ids": ["HP:0001250"], "mode": "both"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["banner"] == BANNER
    assert body["status"] == "not-run"
    assert body["report"]["ranks"] == []
    assert body["report"]["abstained"] is True
    assert "probability" not in body["report"]
    outside = client.post(
        "/run",
        json={"vcf": "/etc/passwd", "hpo_ids": ["HP:0001250"], "mode": "both"},
    )
    assert outside.status_code == 400


def test_pins_are_the_versions_on_the_release_pages() -> None:
    import tomllib

    pins = tomllib.loads((ROOT / "engine" / "pins.toml").read_text(encoding="utf-8"))
    assert pins["exomiser"]["version"] == "15.1.0"
    assert pins["exomiser"]["tag"] == "15.1.0"
    assert pins["lirical"]["version"] == "2.4.1"
    assert pins["lirical"]["tag"] == "v2.4.1"
    exomiser_sha = "47faa54d4791686c9dc3f896762834630e9eaf607ad3cf3399074353c3dda248"
    lirical_sha = "445cd4975e46e6656b5ae2c04785548bbb4c434664c0423332d09bdffeb32248"
    assert exomiser_sha in pins["exomiser"]["sha256"]
    assert lirical_sha in pins["lirical"]["sha256"]

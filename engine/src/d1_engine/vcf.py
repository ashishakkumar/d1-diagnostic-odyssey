"""Build a tiny VCF. A packet is used only when it already has a VCF record."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Variant:
    chrom: str
    pos: int
    ref: str
    alt: str
    gene: str


def variants_from_phenopacket(packet: dict) -> list[Variant]:
    found: list[Variant] = []
    for interpretation in packet.get("interpretations") or []:
        called = interpretation.get("diagnosis") or {}
        for genomic in called.get("genomicInterpretations") or []:
            variant = genomic.get("variantInterpretation") or {}
            described = variant.get("variationDescriptor") or {}
            record = described.get("vcfRecord")
            if not record:
                continue
            gene = str((described.get("geneContext") or {}).get("symbol") or "")
            found.append(
                Variant(
                    chrom=str(record["chrom"]),
                    pos=int(record["pos"]),
                    ref=str(record["ref"]),
                    alt=str(record["alt"]),
                    gene=gene,
                )
            )
    return found


def spike(background: str, variants: list[Variant], decoys: list[str]) -> str:
    lines = background.rstrip("\n").split("\n")
    for variant in variants:
        info = f"GENE={variant.gene}" if variant.gene else "."
        lines.append(
            f"{variant.chrom}\t{variant.pos}\t.\t{variant.ref}\t{variant.alt}\t.\tPASS\t{info}"
        )
    for index, gene in enumerate(decoys, start=1):
        lines.append(f"chr1\t{2000 + index}\t.\tA\tT\t.\tPASS\tGENE={gene}")
    return "\n".join(lines) + "\n"

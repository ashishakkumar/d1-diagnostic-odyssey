# Experimental engine

For research use only. Not for use in diagnostic procedures.

EXPERIMENTAL, RESEARCH ONLY. This process is not the patient notebook. The notebook does not import it and has no route to it. It does not start unless `D1_TRACK=experimental-local` and `engine/ACKNOWLEDGEMENT` both exist. The file is gitignored. Type this line into it, including the final newline:

```text
experimental-local: I understand this engine is research only and must not be used on a real person's data.
```

`D1_TRACK` belongs in `.env`, which is gitignored. Do not point this process at a real person’s VCF.

## What it runs

Exomiser 15.1.0 and LIRICAL 2.4.1, unchanged, from the jars on a volume. Versions, asset names, and the digests reported by the GitHub releases API are in `pins.toml`. See `LICENSES.md` for the AGPL-3.0 code licence, the non-commercial LIRICAL grant, and what is UNCLEAR.

The commands are the documented ones:

```text
java -jar exomiser-cli-15.1.0.jar analyse --analysis job.yml --output-directory out --output-format TSV_GENE
java -jar <lirical jar> phenopacket --assembly hg38 --exomiser-hg38-dir <data> --phenopacket packet.json --vcf in.vcf --output-format tsv -x out/lirical
```

The Exomiser job uses the documented presets `EXOME` and `PHENOTYPE_ONLY`. This repository does not include a variant caller or a pathogenicity classifier. Ranks are the tools’ own scores. A report does not carry a probability: none was calibrated, so there is no reliability curve.

Abstain when the top tool score is not more than twice the next score, or when a phenotype-only ranking and a genotype-only ranking name different first rows. That factor is the catalogue separation, not a cutoff fitted on a cohort.

## Data volume

The multi-gigabyte bundle stays out of git and out of the image. `compose.experimental.yaml` mounts `./data/exomiser` and `./data/lirical` read-only. The container has `network_mode: "none"` and publishes no port. The process binds `127.0.0.1` only.

From the Exomiser install page opened 11 October 2026: the download is approximately 80 GB, and the machine wants at least 100 GB free, preferably on an SSD. Exome analysis is listed at 4 GB RAM minimum. One extracted hg38 variants file is listed at 30G in Exomiser issue 622. Download instructions and the UNCLEAR compatibility notes are in `LICENSES.md`.

This environment did not download the bundle and did not run either tool. It also has no Docker daemon, so the image was not built. Available memory was about 4.8 GB, which is the install page’s exome minimum before the assembly load, so a run was not attempted. No precision or recall from a tool output is reported. The metric functions exist and are tested on planted labels only.

## Hosted build

`D1_BUILD=hosted` (the compose default) has no upload route. It serves `engine/samples/allowlist.txt` only. The one sample is a public synthetic screen, not a tool result.

`D1_BUILD=local` accepts a VCF path that must sit under `D1_INPUT`. It does not accept a file from outside that directory. If the jars are absent, the response is `not-run` and the report has no ranks.

## Not built

A variant caller, a pathogenicity classifier, a second implementation of either tool, a calibrated probability, a notebook button, a literature service, and a copy of the data bundle.

# Licences for the experimental engine

Checked 11 October 2026 from the URLs named here. UNCLEAR means that source was not opened, or it did not yield a licence text. This file is not legal advice. The tools are run unchanged. Their code is not copied into this repository, and the data bundle is not copied into git or into the image.

## Exomiser code

AGPL-3.0.

`https://github.com/exomiser/Exomiser/blob/master/LICENCE`, fetched 11 October 2026, begins “GNU AFFERO GENERAL PUBLIC LICENSE Version 3, 19 November 2007”. The latest GitHub release is tag `15.1.0`, published 2026-06-09. The licence file at that tag was not fetched separately. UNCLEAR whether the tag file differs from master.

The release asset is `exomiser-cli-15.1.0-distribution.zip` (170,449,958 bytes). The GitHub API `digest` was `sha256:47faa54d4791686c9dc3f896762834630e9eaf607ad3cf3399074353c3dda248`. The zip was not downloaded here, so that digest was not recomputed.

Java 21 is required, from the 15.0.0 release notes on the same releases page. This machine has OpenJDK 21.0.10. The internal jar name `exomiser-cli-15.1.0.jar` follows the 15.0.0 release notes’ `exomiser-cli-15.0.0.jar` pattern. The zip was not unpacked, so the internal name is UNCLEAR.

## Exomiser data bundle

Not vendored. Mount it. Do not commit it and do not copy it into the image.

The install page `https://exomiser.readthedocs.io/en/latest/installation.html`, opened 11 October 2026, says the data download is approximately 80 GB and asks for at least 100 GB free, preferably on an SSD. It lists exome analysis at 4 GB RAM minimum, genome analysis at 8 GB RAM minimum, and about 1.5 GB RAM per assembly loaded. It names data version `2602` and the files `2602_phenotype.zip`, `2602_hg19.zip`, and `2602_hg38.zip`.

That page also names CLI `15.1.1`. `https://api.github.com/repos/exomiser/Exomiser/releases/tags/15.1.1` returned HTTP 404 on 11 October 2026. The releases API latest tag is `15.1.0`. The page’s `15.1.1` filename is UNCLEAR.

Discussion `https://github.com/exomiser/Exomiser/discussions/640` (2602 data release, 13 May 2026) lists compatibility with 15.0.0, 14.1.0, and 14.0.0. It does not list 15.1.0. Whether 2602 loads under 15.1.0 is UNCLEAR.

The same discussion names sources inside the bundle, including OMIM 2026-02-12, Orphanet, HPO, gnomAD, ClinVar 2026-02-08, and dbNSFP. It says SpliceAI annotations are free for academic and not-for-profit use, and that other use needs a commercial licence from Illumina, Inc. Issue `https://github.com/exomiser/Exomiser/issues/622` lists an extracted `2602_hg38_variants.mv.db` at 30G.

The notices inside the zip were not read. Per-file terms beyond that discussion are UNCLEAR. OMIM’s own licence text was not opened. UNCLEAR.

The install page’s wget host `g-879a9f.f5dc97.75bc.dn.glob.us` was not requested. Whether that host still serves 2602 is UNCLEAR. The page also points at `https://data.monarchinitiative.org/exomiser/latest`. That directory was not listed. UNCLEAR.

## LIRICAL

Non-commercial. Jackson Laboratory. Non-exclusive, non-transferable, non-sublicensable. The licence says the software is an information resource and should not be relied on for diagnostic or treatment purposes. It also says not to modify the software or create derivative works. This repository does not rebuild LIRICAL.

`https://raw.githubusercontent.com/TheJacksonLaboratory/LIRICAL/master/LICENSE`, fetched 11 October 2026. The file ends `version:6-8-18`. The latest release is `v2.4.1`, published 2026-06-18. The licence file at that tag was not fetched separately. UNCLEAR whether it differs from master.

The release asset is `lirical-cli-2.4.1-distribution.zip` (32,866,100 bytes). The GitHub API digest was `sha256:445cd4975e46e6656b5ae2c04785548bbb4c434664c0423332d09bdffeb32248`. The zip was not downloaded here, so that digest was not recomputed. The jar name inside the zip was not verified. UNCLEAR.

LIRICAL’s tutorial uses an Exomiser data directory. LIRICAL 2.1.0’s release notes say it supports Exomiser database format 2402 or newer. Whether 2.4.1 loads the 2602 bundle was not tested. UNCLEAR. The size of LIRICAL’s own transcript download was not measured. UNCLEAR.

## 1000 Genomes background

Not downloaded and not committed.

`https://www.internationalgenome.org/IGSR_disclaimer/`, opened 11 October 2026: 1000 Genomes data is available without embargo after the project’s final publication. Cite the collection. Rights on other IGSR collections can differ, and the page says users remain responsible for those rights.

Zenodo record `https://zenodo.org/records/3359882` lists `ALL.chr22.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz` at 214.5 MB and an all-chromosome sites VCF at 2.0 GB. Those files are genomes from real people. They are not a fixture in this repository. The committed VCF is a few synthetic lines and is marked `synthetic-background-not-1000-genomes`.

## Phenopacket Store

Not downloaded in this run. A packet is spiked only when it already contains a `vcfRecord`. An HGVS string is not turned into a VCF here.

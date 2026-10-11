"""Loopback screens. A hosted build serves the allowlist and has no upload."""

import html
from pathlib import Path
from typing import Literal

from d1_safety.scan import scan
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, ConfigDict, constr

from d1_engine.gate import BANNER, GRADE, GateError, resolve_bind, start_allowed
from d1_engine.report import build_report
from d1_engine.tools import (
    execute,
    exomiser_argv,
    job_yaml,
    lirical_argv,
    parse_exomiser_genes,
    parse_lirical,
    phenopacket_json,
)

SAMPLES = Path(__file__).resolve().parents[2] / "samples"
Mode = Literal["hosted", "local"]
RunMode = Literal["phenotype", "genotype", "both"]


class RunBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vcf: constr(min_length=1)
    hpo_ids: list[constr(pattern=r"^HP:[0-9]{7}$")]
    mode: RunMode


def _never(mode: Mode) -> None:
    raise GateError(mode)


def _load(root: Path) -> dict[str, str]:
    names = (root / "allowlist.txt").read_text(encoding="utf-8").split()
    found = {name: (root / f"{name}.txt").read_text(encoding="utf-8") for name in names}
    for text in found.values():
        for line in _text(text).splitlines():
            refused = scan(line)
            if refused:
                raise GateError(" ".join(refused))
    return found


def _text(body: str) -> str:
    marked = body if GRADE in body else f"{body.rstrip()}\n{GRADE}\n"
    if marked.startswith(BANNER):
        return marked
    return f"{BANNER}\n{marked}"


def _page(body: str) -> HTMLResponse:
    shown = html.escape(_text(body))
    document = (
        '<!DOCTYPE html><html lang="en"><body>'
        f"<p>{html.escape(BANNER)}</p><pre>{shown}</pre></body></html>"
    )
    return HTMLResponse(document)


def create_app(environ: dict[str, str], ack_path: Path, mode: str) -> FastAPI:
    if not start_allowed(environ, ack_path):
        raise GateError("the engine is not started")
    resolve_bind(environ.get("D1_BIND"))
    chosen: Mode
    if mode == "hosted":
        chosen = "hosted"
    elif mode == "local":
        chosen = "local"
    else:
        raise GateError(mode)
    samples = _load(SAMPLES)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/")
    def home() -> HTMLResponse:
        names = ", ".join(samples)
        return _page(f"Public samples: {names}\n")

    @app.get("/samples/{sample_id}")
    def screen(sample_id: str) -> HTMLResponse:
        if sample_id not in samples:
            return HTMLResponse("missing sample", status_code=404)
        return _page(samples[sample_id])

    @app.get("/samples/{sample_id}/export")
    def export(sample_id: str) -> PlainTextResponse:
        if sample_id not in samples:
            return PlainTextResponse("missing sample", status_code=404)
        return PlainTextResponse(_text(samples[sample_id]))

    if chosen == "hosted":
        return app
    if chosen == "local":

        def _inside(candidate: str) -> Path:
            root = Path(environ.get("D1_INPUT", ""))
            if not root.is_dir():
                raise GateError("input directory is missing")
            path = Path(candidate)
            if not path.is_absolute():
                path = root / path
            resolved = path.resolve()
            if not resolved.is_relative_to(root.resolve()):
                raise GateError("path is outside the input directory")
            return resolved

        @app.post("/run")
        def run(body: RunBody) -> dict[str, object]:
            try:
                _inside(str(body.vcf))
            except GateError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            exomiser = Path(environ.get("EXOMISER_JAR", "/opt/exomiser/exomiser-cli-15.1.0.jar"))
            lirical = Path(environ.get("LIRICAL_JAR", "/opt/lirical/lirical-cli-2.4.1.jar"))
            if not exomiser.is_file() or not lirical.is_file():
                return {
                    "banner": BANNER,
                    "status": "not-run",
                    "report": build_report([]),
                    "reason": "Exomiser or LIRICAL is not on the volume",
                }
            try:
                vcf_path = _inside(str(body.vcf))
                output = Path(environ.get("D1_OUTPUT", "/output"))
                output.mkdir(parents=True, exist_ok=True)
                analysis = output / "job.yml"
                analysis.write_text(
                    job_yaml(vcf=vcf_path, hpo_ids=list(body.hpo_ids), mode=str(body.mode)),
                    encoding="utf-8",
                )
                code = execute(exomiser_argv(jar=exomiser, analysis=analysis, output=output))
                packet = output / "packet.json"
                packet.write_text(
                    phenopacket_json(hpo_ids=list(body.hpo_ids), vcf=vcf_path, mode=str(body.mode)),
                    encoding="utf-8",
                )
                data_dir = Path(environ.get("EXOMISER_DATA", "/data/exomiser/2602_hg38"))
                vcf_arg = None if body.mode == "phenotype" else vcf_path
                lirical_code = execute(
                    lirical_argv(
                        jar=lirical,
                        phenopacket=packet,
                        vcf=vcf_arg,
                        output_prefix=output / "lirical",
                        assembly="hg38",
                        exomiser_dir=data_dir,
                        hpo_ids=list(body.hpo_ids),
                    )
                )
            except OSError:
                return {
                    "banner": BANNER,
                    "status": "not-run",
                    "report": build_report([]),
                    "reason": "the tool output directory could not be written",
                }
            rows: list[dict] = []
            gene_files = sorted(output.glob("*.genes.tsv"))
            if code == 0 and gene_files:
                gene_text = gene_files[0].read_text(encoding="utf-8")
                rows.extend(parse_exomiser_genes(gene_text, version="15.1.0"))
            disease_files = [
                path
                for path in sorted(output.glob("*.tsv"))
                if not path.name.endswith(".genes.tsv")
            ]
            if lirical_code == 0:
                for path in disease_files:
                    disease_text = path.read_text(encoding="utf-8")
                    if "compositeLR" not in disease_text:
                        continue
                    rows.extend(parse_lirical(disease_text, version="2.4.1"))
                    break
            if not rows:
                return {
                    "banner": BANNER,
                    "status": "not-run",
                    "report": build_report([]),
                    "reason": "the tools exited without a rank file",
                }
            return {"banner": BANNER, "status": "tool-output", "report": build_report(rows)}

        return app
    _never(chosen)
    return app

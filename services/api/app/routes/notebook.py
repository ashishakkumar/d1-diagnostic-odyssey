"""Notebook routes. Observations are written only by app.apply_decision."""

import os
from datetime import date
from uuid import UUID, uuid4

import phenopackets.schema.v2 as pps2
import psycopg
from d1_safety.render import SafetyError
from fastapi import FastAPI, HTTPException, Request, Response
from google.protobuf.json_format import ParseDict, ParseError
from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict, constr

from app.demo_cases import DEMO_CASES, case_by_slug, load_demo_case
from app.analyze import analyze as run_analyze
from app.analyze import rerank as run_rerank
from app.pipeline import REVIEWER, build_pipeline, questions_for
from app.routes.ports import (
    country_footer,
    lay_wording,
    prior_for,
    red_flag,
    report_for,
    scan_notebook_text,
)
from app.routes.summary import accepted_rows, pdf_text, summary_text, text_to_pdf
from app.session import apply_decision, bind_reviewer
from d1_contracts import ApprovalRequest, HpoTermDraft, LabReportedVariant, Report

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://d1:d1@127.0.0.1:5432/d1")
SESSION_COOKIE = "d1_session"


class SessionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: constr(min_length=1, strip_whitespace=True)


class VariantBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gene_symbol: constr(min_length=1, strip_whitespace=True)
    variant: constr(min_length=1, strip_whitespace=True)
    lab_words: constr(min_length=1, strip_whitespace=True)
    report_date: date


class TermDraftBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hpo_id: constr(pattern=r"^HP:[0-9]{7}$")
    label: constr(min_length=1, strip_whitespace=True)
    presence: constr(pattern=r"^(present|excluded|uncertain)$")


class DemoCaseOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str
    case_id: str
    title: str
    blurb: str


class DemoListOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cases: list[DemoCaseOut]


class DemoLoadedOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str
    case_id: str


class PipelineIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str | None = None
    note: str | None = None


class AnalyzeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note: constr(min_length=1, max_length=8000)
    use_ai: bool = True


class RerankIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    present: list[constr(pattern=r"^HP:[0-9]{7}$")]
    absent: list[constr(pattern=r"^HP:[0-9]{7}$")] = []


class ConfirmTermIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hpo_id: constr(pattern=r"^HP:[0-9]{7}$")
    label: constr(min_length=1, strip_whitespace=True)


class ConfirmIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: UUID
    terms: list[ConfirmTermIn]


class PopulationPriorOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    experimental: bool
    track: str
    opted_in: bool
    found: bool
    label: str
    limits: str
    source: str | None = None
    version: str | None = None
    population: str | None = None
    variant: str | None = None
    allele_frequency: float | None = None


def _variation(gene_symbol: str, variant: str) -> dict[str, object]:
    descriptor: dict[str, object] = {
        "geneContext": {"symbol": gene_symbol},
        "expressions": [{"syntax": "hgvs", "value": variant}],
    }
    try:
        ParseDict(descriptor, pps2.VariationDescriptor())
    except ParseError as exc:
        raise HTTPException(status_code=422, detail="variant text was refused") from exc
    return descriptor


def _reviewer(request: Request) -> str:
    reviewer = request.cookies.get(SESSION_COOKIE, "").strip()
    if not reviewer:
        raise HTTPException(status_code=401, detail="session missing")
    return reviewer


def _stopped(text: str) -> None:
    screen = red_flag(text)
    if screen is not None:
        raise HTTPException(status_code=409, detail=screen)


def _term_payload(draft_id: str, seen_hash: str, body: dict) -> dict[str, str]:
    plain, fallback = lay_wording(str(body["hpo_id"]), str(body["label"]))
    explanation = str(body["explanation"]) if body.get("explanation") else fallback
    return {
        "draft_id": draft_id,
        "seen_hash": seen_hash,
        "hpo_id": str(body["hpo_id"]),
        "official_name": str(body["label"]),
        "plain_words": plain,
        "explanation": explanation,
        "presence": str(body["presence"]),
    }


def _gate_error(exc: psycopg.Error) -> HTTPException:
    if exc.sqlstate == "23514":
        return HTTPException(status_code=400, detail="seen hash does not match the draft")
    if exc.sqlstate == "55000":
        return HTTPException(status_code=409, detail="draft is not pending")
    if exc.sqlstate == "42501":
        return HTTPException(status_code=401, detail="reviewer is not bound to this transaction")
    return HTTPException(status_code=400, detail="the gate refused the decision")


def create_app() -> FastAPI:
    app = FastAPI(
        title="D1 notebook",
        version="0.0.1",
        description="For research use only. Not for use in diagnostic procedures.",
    )

    @app.post("/session")
    def open_session(body: SessionBody, response: Response) -> dict[str, str]:
        name = str(body.name).strip()
        if not name:
            raise HTTPException(status_code=422, detail="session name missing")
        response.set_cookie(SESSION_COOKIE, name, httponly=True, samesite="lax", path="/")
        return {"name": name}

    @app.get("/footer")
    def footer() -> dict[str, str]:
        return {"text": country_footer()}

    @app.get("/demo/cases", response_model=DemoListOut)
    def demo_cases() -> DemoListOut:
        return DemoListOut(
            cases=[
                DemoCaseOut(
                    slug=str(case["slug"]),
                    case_id=str(case["case_id"]),
                    title=str(case["title"]),
                    blurb=str(case["blurb"]),
                )
                for case in DEMO_CASES
            ]
        )

    @app.post("/demo/cases/{slug}/load", response_model=DemoLoadedOut)
    def load_demo(slug: str, request: Request) -> DemoLoadedOut:
        if case_by_slug(slug) is None:
            raise HTTPException(status_code=404, detail="unknown demo case")
        reviewer = _reviewer(request)
        with psycopg.connect(DATABASE_URL) as connection:
            connection.execute("SET ROLE d1_api")
            try:
                case_id = load_demo_case(connection, slug, reviewer)
            except psycopg.Error as exc:
                raise _gate_error(exc) from exc
        return DemoLoadedOut(slug=slug, case_id=case_id)

    @app.get("/cases/{case_id}/report", response_model=Report, response_model_exclude_unset=True)
    def case_report(case_id: UUID) -> dict:
        accepted = [
            (str(body["hpo_id"]), str(body["presence"]))
            for _at, kind, body in accepted_rows(case_id)
            if kind == "hpo_term" and body.get("hpo_id") and body.get("presence")
        ]
        return report_for(accepted)

    @app.get("/cases/{case_id}/population-prior", response_model=PopulationPriorOut)
    def population_prior(case_id: UUID, opt_in: bool = False) -> PopulationPriorOut:
        variant = ""
        for _at, kind, body in accepted_rows(case_id):
            if kind != "lab_reported_variant":
                continue
            expressions = (body.get("variation") or {}).get("expressions") or []
            if expressions:
                variant = str(expressions[0].get("value") or "")
        return PopulationPriorOut.model_validate(prior_for(variant, opted_in=opt_in))

    @app.post("/cases/{case_id}/term-drafts")
    def create_term_draft(case_id: UUID, body: TermDraftBody) -> dict[str, str]:
        _plain, explanation = lay_wording(str(body.hpo_id), str(body.label))
        _stopped(f"{body.label}\n{explanation}")
        draft_id = uuid4()
        draft = HpoTermDraft(
            id=draft_id,
            case_id=case_id,
            hpo_id=body.hpo_id,
            label=body.label,
            presence=body.presence,
            explanation=explanation,
        )
        stored = draft.model_dump(mode="json", exclude_none=True)
        with psycopg.connect(DATABASE_URL) as connection:
            connection.execute("SET ROLE d1_api")
            row = connection.execute(
                """
                INSERT INTO app.draft (id, case_id, kind, body)
                VALUES (%s, %s, 'hpo_term', %s)
                RETURNING id::text, body_hash
                """,
                (draft_id, case_id, Jsonb(stored)),
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=500, detail="draft was not stored")
        return _term_payload(row[0], row[1], stored)

    @app.get("/cases/{case_id}/term-drafts")
    def list_term_drafts(case_id: UUID) -> dict[str, list[dict[str, str]]]:
        with psycopg.connect(DATABASE_URL) as connection:
            connection.execute("SET ROLE d1_api")
            rows = connection.execute(
                """
                SELECT id::text, body_hash, body
                FROM app.draft
                WHERE case_id = %s AND kind = 'hpo_term' AND status = 'pending'
                ORDER BY created_at DESC
                """,
                (case_id,),
            ).fetchall()
        drafts = []
        for draft_id, seen_hash, body in rows:
            if isinstance(body, dict) and {"hpo_id", "label", "presence"} <= body.keys():
                drafts.append(_term_payload(draft_id, seen_hash, body))
        return {"drafts": drafts}

    @app.get("/cases")
    def list_cases() -> dict[str, list[str]]:
        with psycopg.connect(DATABASE_URL) as connection:
            connection.execute("SET ROLE d1_api")
            rows = connection.execute(
                """
                SELECT case_id::text FROM app.draft
                UNION
                SELECT case_id::text FROM app.observation
                ORDER BY 1
                """
            ).fetchall()
        return {"cases": [row[0] for row in rows]}

    @app.get("/session")
    def read_session(request: Request) -> dict[str, str]:
        reviewer = _reviewer(request)
        return {"name": reviewer}

    @app.post("/cases/{case_id}/variants")
    def create_variant(case_id: UUID, body: VariantBody) -> dict[str, str]:
        _stopped(str(body.lab_words))
        draft_id = uuid4()
        draft = LabReportedVariant(
            id=draft_id,
            case_id=case_id,
            gene_symbol=body.gene_symbol,
            lab_words=body.lab_words,
            report_date=body.report_date,
            variation=_variation(str(body.gene_symbol), str(body.variant)),
        )
        stored = draft.model_dump(mode="json", exclude_none=True)
        with psycopg.connect(DATABASE_URL) as connection:
            connection.execute("SET ROLE d1_api")
            row = connection.execute(
                """
                INSERT INTO app.draft (id, case_id, kind, body)
                VALUES (%s, %s, 'lab_reported_variant', %s)
                RETURNING id::text, body_hash
                """,
                (draft_id, case_id, Jsonb(stored)),
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=500, detail="draft was not stored")
        return {
            "draft_id": row[0],
            "seen_hash": row[1],
            "gene_symbol": str(body.gene_symbol),
            "variant": str(body.variant),
            "lab_words": str(body.lab_words),
            "report_date": body.report_date.isoformat(),
        }

    @app.get("/cases/{case_id}/timeline")
    def timeline(case_id: UUID) -> dict[str, object]:
        rows = accepted_rows(case_id)
        return {
            "case_id": str(case_id),
            "events": [{"at": row[0].isoformat(), "kind": row[1], "body": row[2]} for row in rows],
        }

    @app.get("/cases/{case_id}/summary")
    def summary(case_id: UUID) -> Response:
        try:
            text = summary_text(case_id)
        except SafetyError as exc:
            raise HTTPException(status_code=422, detail="the page failed the scan") from exc
        return Response(content=text, media_type="text/plain; charset=utf-8")

    @app.get("/cases/{case_id}/summary.pdf")
    def summary_pdf(case_id: UUID) -> Response:
        try:
            text = summary_text(case_id)
            pdf = text_to_pdf(text)
            scan_notebook_text(pdf_text(pdf))
        except SafetyError as exc:
            raise HTTPException(status_code=422, detail="the page failed the scan") from exc
        return Response(content=pdf, media_type="application/pdf")

    @app.post("/analyze")
    def analyze_note(body: AnalyzeIn) -> dict[str, object]:
        """Free-text note to ranked rare diseases. The note is not stored."""
        try:
            payload = run_analyze(body.note, body.use_ai)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if isinstance(payload.get("stop"), dict):
            raise HTTPException(status_code=409, detail=payload["stop"])
        return payload

    @app.post("/rerank")
    def rerank(body: RerankIn) -> dict[str, object]:
        """Rank again after the user confirms or corrects HPO terms."""
        return run_rerank(body.present, body.absent)

    @app.get("/ai-status")
    def ai_status() -> dict[str, object]:
        from app import llm_extract

        return {"available": llm_extract.available()}

    @app.post("/pipeline")
    def pipeline(body: PipelineIn) -> dict[str, object]:
        try:
            payload = build_pipeline(body.slug, body.note)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="unknown demo case") from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        screen = payload.get("stop")
        if isinstance(screen, dict):
            raise HTTPException(status_code=409, detail=screen)
        return payload

    @app.post("/pipeline/confirm")
    def confirm_pipeline(body: ConfirmIn, request: Request) -> dict[str, object]:
        if not body.terms:
            raise HTTPException(status_code=422, detail="nothing left to confirm")
        reviewer = request.cookies.get(SESSION_COOKIE, "").strip() or REVIEWER
        recorded: list[str] = []
        kept: list[dict[str, object]] = []
        with psycopg.connect(DATABASE_URL) as connection:
            connection.execute("SET ROLE d1_api")
            bind_reviewer(connection, reviewer)
            for term in body.terms:
                _stopped(term.label)
                plain, explanation = lay_wording(term.hpo_id, term.label)
                draft_id = uuid4()
                draft = HpoTermDraft(
                    id=draft_id,
                    case_id=body.case_id,
                    hpo_id=term.hpo_id,
                    label=term.label,
                    presence="present",
                    explanation=explanation,
                )
                stored = draft.model_dump(mode="json", exclude_none=True)
                row = connection.execute(
                    """
                    INSERT INTO app.draft (id, case_id, kind, body)
                    VALUES (%s, %s, 'hpo_term', %s)
                    RETURNING body_hash
                    """,
                    (draft_id, body.case_id, Jsonb(stored)),
                ).fetchone()
                if row is None:
                    raise HTTPException(status_code=500, detail="draft was not stored")
                try:
                    apply_decision(connection, str(draft_id), "approve", row[0])
                except psycopg.Error as exc:
                    raise _gate_error(exc) from exc
                recorded.append(str(draft_id))
                kept.append({"hpo_id": term.hpo_id, "plain_words": plain, "label": term.label})
        return {
            "case_id": str(body.case_id),
            "reviewer": reviewer,
            "recorded": recorded,
            "questions": questions_for(kept),
        }

    @app.post("/cases/{case_id}/approvals")
    def approve(case_id: UUID, body: ApprovalRequest, request: Request) -> dict[str, str]:
        reviewer = _reviewer(request)
        with psycopg.connect(DATABASE_URL) as connection:
            connection.execute("SET ROLE d1_api")
            found = connection.execute(
                "SELECT case_id::text, kind, body FROM app.draft WHERE id = %s::uuid",
                (body.draft_id,),
            ).fetchone()
            if found is None or found[0] != str(case_id):
                raise HTTPException(status_code=404, detail="draft not found")
            stored = found[2] if isinstance(found[2], dict) else {}
            if (
                body.decision == "approve"
                and found[1] == "hpo_term"
                and stored.get("presence") == "uncertain"
            ):
                raise HTTPException(status_code=422, detail="uncertain is not an accepted presence")
            bind_reviewer(connection, reviewer)
            try:
                decision_id = apply_decision(
                    connection, str(body.draft_id), body.decision, body.seen_hash
                )
            except psycopg.Error as exc:
                raise _gate_error(exc) from exc
        return {"decision_id": decision_id}

    return app


app = create_app()

"use client";

import { SymptomReview, type TermDraftView } from "@/components/term-accept";
import { Button } from "@/components/ui/button";
import type { ApprovalRequest } from "@/src/index";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

const SYNTHETIC_TERM = {
  hpo_id: "HP:0001250",
  label: "Seizure",
  presence: "present",
};

export default function SymptomsPage() {
  const params = useParams<{ id: string }>();
  const [drafts, setDrafts] = useState<TermDraftView[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    const response = await fetch(`/api/cases/${params.id}/term-drafts`);
    if (!response.ok) {
      setMessage("The notebook cannot reach the API.");
      return;
    }
    const body = (await response.json()) as { drafts: TermDraftView[] };
    setDrafts(body.drafts);
  }, [params.id]);

  useEffect(() => {
    void load();
  }, [load]);

  async function decide(body: ApprovalRequest) {
    const response = await fetch(`/api/cases/${params.id}/approvals`, {
      method: "POST",
      credentials: "include",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const detail = (await response.json().catch(() => ({}))) as { detail?: string };
      setMessage(detail.detail ?? "The decision was not saved.");
      return;
    }
    setMessage(body.decision === "approve" ? "Accepted." : "Rejected.");
    await load();
  }

  return (
    <section className="space-y-4">
      <h1 className="text-2xl">Drafted symptoms</h1>
      <p>Accept or reject each drafted term. This is a form.</p>
      <Button
        type="button"
        variant="secondary"
        onClick={async () => {
          const response = await fetch(`/api/cases/${params.id}/term-drafts`, {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify(SYNTHETIC_TERM),
          });
          if (response.status === 409) {
            const payload = (await response.json()) as {
              detail?: { title?: string; body?: string; footer?: string };
            };
            const detail = payload.detail;
            setMessage(
              [detail?.title, detail?.body, detail?.footer].filter(Boolean).join(" ") ||
                "Stop. The words were not saved.",
            );
            return;
          }
          if (!response.ok) {
            setMessage("The synthetic term was not saved.");
            return;
          }
          setMessage(null);
          await load();
        }}
      >
        Load one synthetic drafted term
      </Button>
      {message ? <p>{message}</p> : null}
      <SymptomReview drafts={drafts} onDecide={(body) => void decide(body)} />
    </section>
  );
}

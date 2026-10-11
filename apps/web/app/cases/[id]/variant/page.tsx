"use client";

import { DecisionButtons } from "@/components/term-accept";
import { Button } from "@/components/ui/button";
import { VariantForm, type VariantFields } from "@/components/variant-form";
import type { ApprovalRequest } from "@/src/index";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

type PendingVariant = VariantFields & { draft_id: string; seen_hash: string };

async function stopText(response: Response): Promise<string> {
  const payload = (await response.json()) as {
    detail?: { title?: string; body?: string; footer?: string };
  };
  const detail = payload.detail;
  return (
    [detail?.title, detail?.body, detail?.footer].filter(Boolean).join(" ") ||
    "Stop. The words were not saved."
  );
}

export default function VariantPage() {
  const params = useParams<{ id: string }>();
  const [pending, setPending] = useState<PendingVariant | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    setReady(true);
  }, []);

  async function save(fields: VariantFields) {
    const response = await fetch(`/api/cases/${params.id}/variants`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(fields),
    });
    if (response.status === 409) {
      setMessage(await stopText(response));
      return;
    }
    if (!response.ok) {
      setMessage("The variant was not saved.");
      return;
    }
    const draft = (await response.json()) as PendingVariant;
    setPending({ ...fields, draft_id: draft.draft_id, seen_hash: draft.seen_hash });
    setMessage("Check the words, then accept or reject them.");
  }

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
    setPending(null);
    setMessage(body.decision === "approve" ? "Added to the notebook." : "Not kept.");
  }

  return (
    <section className="space-y-4">
      <h1 className="text-2xl">Lab-reported variant</h1>
      <VariantForm onSubmit={(fields) => void save(fields)} />
      <Button
        type="button"
        variant="secondary"
        disabled={!ready}
        onClick={() =>
          void save({
            gene_symbol: "FBN1",
            variant: "NM_000138.5:c.1A>G",
            lab_words: "Unconsciousness.",
            report_date: "2024-03-01",
          })
        }
      >
        Try a warning-sign phrase
      </Button>
      {message ? <p>{message}</p> : null}
      {pending ? (
        <div className="space-y-2 rounded-md border border-border p-4">
          <p>
            Gene {pending.gene_symbol}. Variant {pending.variant}. Report date {pending.report_date}.
          </p>
          <p>The lab&apos;s words: {pending.lab_words}</p>
          <p className="text-sm text-muted-foreground">Hash {pending.seen_hash.slice(0, 12)}</p>
          <DecisionButtons
            draftId={pending.draft_id}
            seenHash={pending.seen_hash}
            onDecide={(body) => void decide(body)}
          />
        </div>
      ) : null}
    </section>
  );
}

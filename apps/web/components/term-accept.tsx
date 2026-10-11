import type { ApprovalRequest } from "@/src/index";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export type TermDraftView = {
  draft_id: string;
  seen_hash: string;
  hpo_id: string;
  official_name: string;
  plain_words: string;
  explanation: string;
  presence: "present" | "excluded" | "uncertain";
};

export function DecisionButtons({
  draftId,
  seenHash,
  onDecide,
}: {
  draftId: string;
  seenHash: string;
  onDecide: (body: ApprovalRequest) => void;
}) {
  const send = (decision: ApprovalRequest["decision"]) => {
    const body: ApprovalRequest = { draft_id: draftId, decision, seen_hash: seenHash };
    onDecide(body);
  };
  return (
    <div className="flex gap-2">
      <Button type="button" onClick={() => send("approve")}>
        Accept
      </Button>
      <Button type="button" variant="outline" onClick={() => send("reject")}>
        Reject
      </Button>
    </div>
  );
}

export function SymptomReview({
  drafts,
  onDecide,
}: {
  drafts: TermDraftView[];
  onDecide: (body: ApprovalRequest) => void;
}) {
  if (drafts.length === 0) {
    return <p>No drafted term is waiting.</p>;
  }
  return (
    <ul className="space-y-4">
      {drafts.map((term) => (
        <li key={term.draft_id} className="ed-paper space-y-2 p-5">
          <p className="font-display text-xl italic text-[var(--ed-fg)]">{term.plain_words}</p>
          <p>
            Official name: {term.official_name} ({term.hpo_id})
          </p>
          <p>{term.explanation}</p>
          <Badge>{term.presence}</Badge>
          <p className="text-sm text-muted-foreground">
            Hash <span>{term.seen_hash.slice(0, 12)}</span>
          </p>
          <DecisionButtons draftId={term.draft_id} seenHash={term.seen_hash} onDecide={onDecide} />
        </li>
      ))}
    </ul>
  );
}

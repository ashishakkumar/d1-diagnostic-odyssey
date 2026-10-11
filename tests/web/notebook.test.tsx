import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderToString } from "react-dom/server";
import { expect, test, vi } from "vitest";
import type { ApprovalRequest } from "../../apps/web/src/index.ts";
import { CaseList } from "../../apps/web/components/case-list.tsx";
import { SessionForm } from "../../apps/web/components/session-form.tsx";
import { SummaryPreview } from "../../apps/web/components/summary-preview.tsx";
import { SymptomReview } from "../../apps/web/components/term-accept.tsx";
import { TimelineList } from "../../apps/web/components/timeline-list.tsx";
import { VariantForm } from "../../apps/web/components/variant-form.tsx";
import { NotebookShell } from "../../apps/web/components/notebook-shell.tsx";
import VariantPage from "../../apps/web/app/cases/[id]/variant/page.tsx";

const TERM = {
  draft_id: "00000000-0000-4000-8000-0000000000b1",
  seen_hash: "ab".repeat(32),
  hpo_id: "HP:0001250",
  official_name: "Seizure",
  plain_words: "seizures",
  explanation: "A burst of brain activity that changes movement.",
  presence: "present" as const,
};

test("the footer notice stays on the page shell", () => {
  render(
    <NotebookShell>
      <p>timeline</p>
    </NotebookShell>,
  );
  expect(screen.getByText("timeline")).toBeInTheDocument();
  const footer = screen.getByRole("contentinfo");
  expect(footer).toHaveTextContent("For research use only.");
  expect(footer).toHaveTextContent("Not for use in diagnostic procedures.");
  expect(footer).toHaveTextContent("Not a diagnosis");
});

test("an empty case list says no synthetic case is loaded", () => {
  render(<CaseList cases={[]} error={null} />);
  expect(screen.getByText("No synthetic case loaded.")).toBeInTheDocument();
});

test("a down API is an error state, not an empty notebook", () => {
  render(<CaseList cases={[]} error="down" />);
  expect(screen.getByText("The notebook cannot reach the API.")).toBeInTheDocument();
});

test("the session form sends the typed name", async () => {
  const user = userEvent.setup();
  const names: string[] = [];
  render(<SessionForm onSubmit={(name) => names.push(name)} />);
  await user.type(screen.getByLabelText("Your name for this notebook"), "caregiver");
  await user.click(screen.getByRole("button", { name: "Continue" }));
  expect(names).toEqual(["caregiver"]);
});

test("a drafted term shows plain words, the official name, and a short explanation", () => {
  render(<SymptomReview drafts={[TERM]} onDecide={() => {}} />);
  expect(screen.getByText("seizures")).toBeInTheDocument();
  expect(screen.getByText(/Official name: Seizure \(HP:0001250\)/)).toBeInTheDocument();
  expect(screen.getByText(TERM.explanation)).toBeInTheDocument();
  expect(screen.getByText(TERM.seen_hash.slice(0, 12))).toBeInTheDocument();
});

test("accept and reject post an ApprovalRequest", async () => {
  const user = userEvent.setup();
  const seen: ApprovalRequest[] = [];
  render(<SymptomReview drafts={[TERM]} onDecide={(body) => seen.push(body)} />);
  await user.click(screen.getByRole("button", { name: "Accept" }));
  await user.click(screen.getByRole("button", { name: "Reject" }));
  expect(seen).toEqual([
    { draft_id: TERM.draft_id, decision: "approve", seen_hash: TERM.seen_hash },
    { draft_id: TERM.draft_id, decision: "reject", seen_hash: TERM.seen_hash },
  ]);
  expect(Object.keys(seen[0]).sort()).toEqual(["decision", "draft_id", "seen_hash"]);
});

test("no drafted term is an empty state", () => {
  render(<SymptomReview drafts={[]} onDecide={() => {}} />);
  expect(screen.getByText("No drafted term is waiting.")).toBeInTheDocument();
});

test("the timeline keeps the order it was given", () => {
  render(
    <TimelineList
      events={[
        {
          at: "2024-02-02T00:00:00+00:00",
          kind: "hpo_term",
          body: { label: "Hypotonia", hpo_id: "HP:0001252", presence: "present" },
        },
        {
          at: "2024-01-01T00:00:00+00:00",
          kind: "lab_reported_variant",
          body: {
            gene_symbol: "EXAMPLE1",
            lab_words: "the synthetic report's own words",
            report_date: "2024-03-01",
            variation: { expressions: [{ value: "c.1A>G" }] },
          },
        },
      ]}
    />,
  );
  const rows = screen.getAllByRole("row");
  expect(rows[1]).toHaveTextContent("Hypotonia");
  expect(rows[1]).toHaveTextContent("HP:0001252");
  expect(rows[2]).toHaveTextContent("EXAMPLE1");
  expect(rows[2]).toHaveTextContent("c.1A>G");
  expect(rows[2]).toHaveTextContent("the synthetic report's own words");
});

test("an empty timeline says nothing has been accepted", () => {
  render(<TimelineList events={[]} />);
  expect(screen.getByText("Nothing has been accepted on this case yet.")).toBeInTheDocument();
});

test("the variant form sends gene, variant, the lab's words, and the date", async () => {
  const user = userEvent.setup();
  const seen: Array<Record<string, string>> = [];
  render(<VariantForm onSubmit={(fields) => seen.push(fields)} />);
  expect(screen.queryByLabelText(/classification/i)).toBeNull();
  expect(screen.getByText(/does not classify/i)).toBeInTheDocument();
  await user.type(screen.getByLabelText("Gene, as written on the report"), "EXAMPLE1");
  await user.type(screen.getByLabelText("Variant, as written on the report"), "c.1A>G");
  await user.type(screen.getByLabelText("The lab's own words"), "the synthetic report's own words");
  await user.type(screen.getByLabelText("Report date"), "2024-03-01");
  await user.click(screen.getByRole("button", { name: "Save what I typed" }));
  expect(seen).toEqual([
    {
      gene_symbol: "EXAMPLE1",
      variant: "c.1A>G",
      lab_words: "the synthetic report's own words",
      report_date: "2024-03-01",
    },
  ]);
});

test("the summary preview shows the template text and a PDF link", () => {
  render(
    <SummaryPreview
      text={"Questions to take to a doctor\nNot for use in diagnostic procedures."}
      pdfHref="/api/cases/1/summary.pdf"
    />,
  );
  expect(screen.getByText(/Questions to take to a doctor/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Download the one-to-two-page PDF" })).toHaveAttribute(
    "href",
    "/api/cases/1/summary.pdf",
  );
});

test("the warning-sign button is disabled until the page is mounted", () => {
  const html = renderToString(<VariantPage />);
  const button = new DOMParser()
    .parseFromString(html, "text/html")
    .querySelector("button[type='button']");
  expect(button?.textContent).toBe("Try a warning-sign phrase");
  expect(button?.hasAttribute("disabled")).toBe(true);
});

test("a warning-sign phrase shows the stop screen", async () => {
  const user = userEvent.setup();
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      status: 409,
      ok: false,
      json: async () => ({
        detail: {
          title: "Stop",
          body: "Stop. Your words match this warning sign: Unconsciousness.",
          footer: "Call 112.",
        },
      }),
    })),
  );
  try {
    render(<VariantPage />);
    await user.click(screen.getByRole("button", { name: "Try a warning-sign phrase" }));
    expect(await screen.findByText(/Unconsciousness/)).toBeInTheDocument();
    expect(screen.getByText(/Call 112/)).toBeInTheDocument();
  } finally {
    vi.unstubAllGlobals();
  }
});

test("a warning-sign request that never reaches the API says so", async () => {
  const user = userEvent.setup();
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      throw new Error("down");
    }),
  );
  try {
    render(<VariantPage />);
    await user.click(screen.getByRole("button", { name: "Try a warning-sign phrase" }));
    expect(await screen.findByText(/cannot reach the API/)).toBeInTheDocument();
  } finally {
    vi.unstubAllGlobals();
  }
});

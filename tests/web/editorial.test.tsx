import { render, screen, within } from "@testing-library/react";
import { expect, test } from "vitest";
import { EvidenceGrid } from "../../apps/web/components/editorial/evidence-grid.tsx";
import LandingPage from "../../apps/web/app/page.tsx";

const EV = [
  { hpo_id: "HP:1", orphanet_id: "ORPHA:1", relation: "supports", source: "s", version: "v" },
  { hpo_id: "HP:2", orphanet_id: "ORPHA:1", relation: "supports", source: "s", version: "v" },
  { hpo_id: "HP:1", orphanet_id: "ORPHA:2", relation: "does_not_support", source: "s", version: "v" },
  { hpo_id: "HP:2", orphanet_id: "ORPHA:2", relation: "supports", source: "s", version: "v" },
];

test("the evidence grid puts the leading entry first and labels every cell", () => {
  render(<EvidenceGrid evidence={EV} leadingId="ORPHA:1" termLabels={{ "HP:1": "Seizure" }} />);
  const rows = screen.getAllByRole("row");
  expect(rows[1]).toHaveTextContent("ORPHA:1");
  expect(rows[1]).toHaveTextContent("leads");
  expect(within(rows[2]).getAllByRole("img").map((el) => el.getAttribute("aria-label"))).toEqual([
    "does not fit or not listed",
    "fits",
  ]);
  expect(screen.getByText("Seizure")).toBeInTheDocument();
});

test("an abstained grid does not mark a leader", () => {
  render(<EvidenceGrid evidence={EV} />);
  expect(screen.queryByText("leads")).not.toBeInTheDocument();
});

test("the landing page says what it is, what it is not, and what was not measured", () => {
  render(<LandingPage />);
  expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/rare-disease diagnosis/);
  expect(screen.getAllByText(/Not a diagnostic tool/i).length).toBeGreaterThan(0);
  expect(screen.getByText("Not measured")).toBeInTheDocument();
  expect(screen.getByText(/Whether any family reaches a diagnosis sooner/)).toBeInTheDocument();
  expect(screen.getByTestId("measured-bars")).toHaveTextContent("45.3%");
  expect(screen.getByTestId("measured-bars")).toHaveTextContent("35.4%");
});

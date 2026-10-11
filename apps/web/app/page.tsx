import { EvidenceGrid } from "@/components/editorial/evidence-grid";
import { Lane, MeasuredBars, OdysseyIllustration } from "@/components/editorial/figures";
import { Section } from "@/components/editorial/section";
import { StartDemo } from "@/components/editorial/start-demo";
import Link from "next/link";

const SAMPLE_LABELS = { "HP:0000272": "Malar flattening", "HP:0001166": "Arachnodactyly" };
const SUPPORT = (hpo_id: string, orphanet_id: string, relation: "supports" | "does_not_support") => ({
  hpo_id,
  orphanet_id,
  relation,
  source: "orphanet-en_product4",
  version: "2026-06-23-synthetic",
});
// Copied from the synthetic case "Separated rows" (catalogue ids are made up).
const SAMPLE_EVIDENCE = [
  SUPPORT("HP:0000272", "ORPHA:9000001", "supports"),
  SUPPORT("HP:0001166", "ORPHA:9000001", "supports"),
  SUPPORT("HP:0000272", "ORPHA:9000002", "does_not_support"),
  SUPPORT("HP:0001166", "ORPHA:9000002", "supports"),
  SUPPORT("HP:0000272", "ORPHA:9000011", "does_not_support"),
  SUPPORT("HP:0001166", "ORPHA:9000011", "does_not_support"),
  SUPPORT("HP:0000272", "ORPHA:9000012", "does_not_support"),
  SUPPORT("HP:0001166", "ORPHA:9000012", "does_not_support"),
  SUPPORT("HP:0000272", "ORPHA:9000021", "does_not_support"),
  SUPPORT("HP:0001166", "ORPHA:9000021", "does_not_support"),
];

const FACTS: Array<[string, string]> = [
  ["What it is", "A private notebook and a one-page handout for a doctor visit."],
  ["Who it is for", "A patient or caregiver who keeps the record. A clinician reads the page they bring."],
  ["What goes in", "Symptoms you accept, in plain words. A genetic variant, if you copy one word for word from a lab report."],
  ["How it decides", "Plain arithmetic over public rare-disease catalogue data. No AI model is called on this path. Every sentence on the page is a fixed template."],
  ["What comes out", "A comparison that shows its sources and versions, or says it cannot separate the entries. Then questions to ask."],
  ["Data used", "Orphanet and the Human Phenotype Ontology. Tested on Phenopacket Store 0.1.27."],
  ["Not for", "Diagnosis, emergencies, choosing a treatment or a dose, or reading genome files."],
  ["Status", "Research prototype. Synthetic cases only. Not used with any patient."],
];

export default function LandingPage() {
  return (
    <div>
      {/* 1. Hero: what it is, who for, in the first screen */}
      <section className="ed-shell pt-14 pb-12 md:pt-24 md:pb-16">
        <p className="font-mono-label">Case study · Healthcare AI · Research prototype</p>
        <h1 className="hero-title mt-5 max-w-[18ch]">A notebook for the search for a <span className="whitespace-nowrap">rare-disease</span> diagnosis.</h1>
        <p className="deck mt-6 max-w-[40ch] md:max-w-[52ch]">
          You confirm each symptom in plain words. The notebook lines them up against public rare-disease catalogues,
          shows why each entry fits or does not, and says so plainly when it cannot tell them apart. Then it writes a
          one-page list of questions for your doctor.
        </p>
        <ul className="mt-6 flex flex-wrap gap-2" aria-label="Status">
          {["Research prototype", "Synthetic data only", "Not a diagnostic tool"].map((t) => (
            <li
              key={t}
              className="border border-border bg-[var(--ed-bg-elev)] px-2.5 py-1 font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.12em] text-[var(--ed-fg-soft)]"
            >
              {t}
            </li>
          ))}
        </ul>
        <div className="mt-9 flex flex-wrap items-start gap-x-6 gap-y-4">
          <StartDemo />
          <Link href="#how" className="ed-btn ed-btn-ghost no-underline">
            See how it works
          </Link>
        </div>
        <div className="mt-14 md:mt-20">
          <OdysseyIllustration />
        </div>
      </section>

      {/* 2. Problem */}
      <Section id="problem" label="The problem" title="Rare diseases are found slowly, and the family carries the story.">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-[1.1fr_1fr] md:gap-14">
          <div className="prose-ed space-y-5">
            <p>
              Someone with an unexplained, long-running set of symptoms sees one clinic, then another. Each visit starts
              from the top. The person living with it ends up being the only one who holds the whole history.
            </p>
            <p>
              A 2022 survey of 6,507 people in Europe with a confirmed rare disease measured how long that takes. It is a
              volunteer survey of people who did eventually get a diagnosis, so it cannot count those still waiting.
            </p>
            <p className="text-[0.875rem] text-muted-foreground">
              Source:{" "}
              <a
                className="underline hover:text-[var(--ed-accent)]"
                href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11369105/"
              >
                Faye et al., European Journal of Human Genetics, 2024
              </a>{" "}
              (EURORDIS Rare Barometer).
            </p>
          </div>
          <dl className="grid grid-cols-1 gap-px border border-border bg-[var(--ed-line)]">
            {[
              ["4.7 years", "average time from first symptoms to a confirmed diagnosis. The median was 0.8 years: many are quick, some take very long."],
              ["1 in 4", "waited five years or more."],
              ["73%", "said they were misdiagnosed at least once. The survey counts symptoms put down to another illness, brushed off, or called psychological."],
            ].map(([figure, text]) => (
              <div key={figure} className="bg-[var(--ed-bg)] p-5">
                <dt className="font-display text-4xl italic text-[var(--ed-accent)]">{figure}</dt>
                <dd className="mt-1 text-[0.9375rem] leading-snug text-[var(--ed-fg-soft)]">{text}</dd>
              </div>
            ))}
          </dl>
        </div>
      </Section>

      {/* 3. What it is — facts label */}
      <Section label="The idea" title="One place to confirm what you have actually seen, in words a doctor can check.">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-[1fr_1.2fr] md:gap-14">
          <div className="prose-ed space-y-5">
            <p>
              The notebook does not try to be the doctor. It is a careful record keeper. Nothing enters the record until
              the person accepts it, and nothing leaves it except a short page with its sources attached.
            </p>
            <p>
              The facts label follows the idea of a{" "}
              <a
                className="underline hover:text-[var(--ed-accent)]"
                href="https://www.nature.com/articles/s41746-020-0253-3"
              >
                “Model Facts” label
              </a>
              : intended use, method, data and limits on one page, before anyone is asked to trust the output.
            </p>
          </div>
          <div className="ed-paper p-5 sm:p-7" aria-label="Facts label">
            <p className="font-mono-label">Facts label · Diagnostic Odyssey</p>
            <dl className="mt-4 divide-y divide-[var(--ed-line)]">
              {FACTS.map(([k, v]) => (
                <div key={k} className="grid gap-1 py-3 sm:grid-cols-[8.5rem_1fr] sm:gap-4">
                  <dt className="font-mono-label pt-1">{k}</dt>
                  <dd className="text-[0.9375rem] leading-snug text-[var(--ed-fg)]">{v}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </Section>

      {/* 4. How it works */}
      <Section id="how" label="How it works" title="Three steps, and who does the work at each.">
        <ol className="grid grid-cols-1 gap-px border border-border bg-[var(--ed-line)] md:grid-cols-3">
          {[
            {
              n: "1",
              h: "You confirm symptoms",
              p: "Each symptom appears in plain words next to its official name from the Human Phenotype Ontology. You accept or reject it. Until you accept it, it is not in the record.",
              who: "You decide",
              what: "what goes in",
            },
            {
              n: "2",
              h: "Code compares them",
              p: "The accepted symptoms are compared with Orphanet rare-disease entries and their published frequencies. If ten or more entries sit within a factor of two of each other, it abstains rather than pick one.",
              who: "Code, no AI model",
              what: "does the arithmetic",
            },
            {
              n: "3",
              h: "A page for your doctor",
              p: "A one-to-two-page PDF: what you confirmed, what the comparison showed with sources and versions, and questions to ask. Every sentence is a fixed template that says it is not a diagnosis.",
              who: "Fixed template",
              what: "writes the words",
            },
          ].map((s) => (
            <li key={s.n} className="bg-[var(--ed-bg)] p-6">
              <span className="num text-sm text-[var(--ed-accent)]">0{s.n}</span>
              <h3 className="font-display mt-2 text-2xl italic">{s.h}</h3>
              <p className="mt-3 text-[0.9375rem] leading-relaxed text-[var(--ed-fg-soft)]">{s.p}</p>
              <Lane who={s.who}>{s.what}</Lane>
            </li>
          ))}
        </ol>
        <p className="mt-6 max-w-[62ch] text-[0.9375rem] text-[var(--ed-fg-soft)]">
          A variant typed from a lab report is stored word for word. It is not an input to the comparison, and the
          notebook does not classify it.
        </p>
      </Section>

      {/* 5. Guided walk-through */}
      <Section id="walkthrough" label="A synthetic case" title="Follow one made-up case from symptoms to the page.">
        <ol className="space-y-12">
          <li className="grid grid-cols-1 gap-6 md:grid-cols-[14rem_minmax(0,1fr)] md:gap-10">
            <div>
              <p className="num text-sm text-[var(--ed-accent)]">Step 1</p>
              <h3 className="font-display mt-1 text-xl italic">Terms the person accepted</h3>
              <p className="mt-2 text-[0.9375rem] text-[var(--ed-fg-soft)]">Two symptoms, in plain words.</p>
            </div>
            <ul className="grid gap-3 sm:grid-cols-2">
              {[
                ["Cheeks that look flatter than usual", "Malar flattening", "HP:0000272"],
                ["Fingers that are long for the hand", "Arachnodactyly", "HP:0001166"],
              ].map(([plain, official, id]) => (
                <li key={id} className="ed-paper p-4">
                  <p className="font-display text-lg">{plain}</p>
                  <p className="mt-1 text-[0.8125rem] text-[var(--ed-fg-soft)]">
                    {official} · <span className="num">{id}</span> · marked present
                  </p>
                </li>
              ))}
            </ul>
          </li>
          <li className="grid grid-cols-1 gap-6 md:grid-cols-[14rem_minmax(0,1fr)] md:gap-10">
            <div>
              <p className="num text-sm text-[var(--ed-accent)]">Step 2</p>
              <h3 className="font-display mt-1 text-xl italic">What the comparison shows</h3>
              <p className="mt-2 text-[0.9375rem] text-[var(--ed-fg-soft)]">
                One entry fits both symptoms. The next fits one. The rest fit neither. The catalogue ids are invented for
                the demo.
              </p>
            </div>
            <EvidenceGrid evidence={SAMPLE_EVIDENCE} termLabels={SAMPLE_LABELS} leadingId="ORPHA:9000001" maxRows={4} />
          </li>
          <li className="grid grid-cols-1 gap-6 md:grid-cols-[14rem_minmax(0,1fr)] md:gap-10">
            <div>
              <p className="num text-sm text-[var(--ed-accent)]">Step 3</p>
              <h3 className="font-display mt-1 text-xl italic">The page for the doctor</h3>
              <p className="mt-2 text-[0.9375rem] text-[var(--ed-fg-soft)]">An excerpt of the generated page.</p>
            </div>
            <blockquote className="ed-paper m-0 p-5 sm:p-6">
              <p className="font-mono-label">Questions to take to a doctor</p>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-[0.9375rem] text-[var(--ed-fg)]">
                <li>I confirmed Malar flattening (HP:0000272). What should we discuss about that term?</li>
                <li>I confirmed Arachnodactyly (HP:0001166). What should we discuss about that term?</li>
              </ul>
              <p className="mt-4 border-t border-border pt-3 text-[0.8125rem] text-[var(--ed-fg-soft)]">
                Catalogue comparison. First row ORPHA:9000001. This is not a diagnosis.
              </p>
            </blockquote>
          </li>
        </ol>
        <div className="mt-12 flex flex-wrap items-center gap-6">
          <StartDemo label="Open this case live" />
          <Link href="/notebook" className="text-sm text-[var(--ed-fg-soft)] underline hover:text-[var(--ed-accent)]">
            or start from the notebook
          </Link>
        </div>
      </Section>

      {/* 6. Impact — measured vs not measured */}
      <Section id="impact" label="What has been measured" title="One ranking test on public data. Nothing yet about patients.">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-[1.15fr_minmax(0,1fr)] md:gap-14">
          <MeasuredBars />
          <div className="prose-ed space-y-6">
            <div>
              <p className="font-mono-label">Measured</p>
              <p className="mt-2">
                On 925 held-out public cases, the shipped ranker put the documented disease first about 45% of the time,
                against about 35% for a simple baseline.
              </p>
              <p className="mt-3">
                An earlier, simpler frequency comparison did <em>not</em> beat that baseline (29.0% against 34.2% for
                first place, on all packets). That result is kept in the repository, and it is why the public-case ranker
                was changed.
              </p>
            </div>
            <div>
              <p className="font-mono-label">Not measured</p>
              <ul className="mt-2 list-disc space-y-1.5 pl-5">
                <li>Whether any family reaches a diagnosis sooner.</li>
                <li>Whether people understand the page, or whether doctors find it useful.</li>
                <li>Performance on real clinic notes, or on the 531 of 780 diseases that were left out.</li>
                <li>Regulatory status. It is left open.</li>
              </ul>
            </div>
          </div>
        </div>
      </Section>

      {/* 7. Limits */}
      <Section id="limits" label="Honest limits" title="What this does not do.">
        <ul className="grid grid-cols-1 gap-px border border-border bg-[var(--ed-line)] sm:grid-cols-2">
          {[
            ["It does not diagnose.", "It cannot rule a disease in or out, and it never suggests a treatment or a dose."],
            ["It does not read genomes.", "A variant is copied from a lab report as text. It is stored and shown, never scored."],
            ["The demo uses made-up catalogue entries.", "The five demo stories run a simpler frequency card on invented ids. The stronger ranker was measured on public cases and is not what the demo screen computes."],
            ["The hosted demo is shared.", "Everyone who opens it sees and edits the same synthetic data. Real records would stay on the person’s own computer."],
            ["It is not for emergencies.", "If someone is unwell right now, call the local emergency number. In India that is 112."],
            ["It has not met a patient.", "No user study, no clinician review, no clinical claim."],
          ].map(([h, p]) => (
            <li key={h} className="bg-[var(--ed-bg)] p-5">
              <p className="font-display text-lg italic text-[var(--ed-fg)]">{h}</p>
              <p className="mt-1.5 text-[0.9375rem] leading-snug text-[var(--ed-fg-soft)]">{p}</p>
            </li>
          ))}
        </ul>
        <p className="mt-8 max-w-[62ch] text-[0.9375rem] text-[var(--ed-fg-soft)]">
          Whether software like this counts as a medical device is a regulatory question this project does not answer.
          FDA’s{" "}
          <a
            className="underline hover:text-[var(--ed-accent)]"
            href="https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software"
          >
            January 2026 clinical decision support guidance
          </a>{" "}
          is the reason the page shows its inputs, method and data.
        </p>
      </Section>
    </div>
  );
}

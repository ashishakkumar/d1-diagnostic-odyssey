/**
 * Hand-drawn SVG and CSS figures. Abstract on purpose: no people, no patient data.
 * Colours come from the Editorial tokens.
 */

export function OdysseyIllustration() {
  // A winding line with clinic-visit nodes between "first symptoms" and "diagnosis".
  const stops: Array<[number, number, number]> = [
    [110, 120, 5],
    [215, 62, 5],
    [330, 150, 5],
    [430, 70, 5],
    [545, 138, 5],
    [640, 58, 5],
    [740, 128, 5],
  ];
  return (
    <figure className="m-0">
      <svg
        viewBox="0 0 960 200"
        role="img"
        aria-label="Illustration: a winding path with many stops between first symptoms and a confirmed diagnosis."
        className="h-auto w-full"
      >
        <line x1="40" y1="176" x2="920" y2="176" stroke="var(--ed-line)" strokeWidth="1" />
        <line x1="40" y1="170" x2="40" y2="182" stroke="var(--ed-fg-mute)" strokeWidth="1" />
        <line x1="920" y1="170" x2="920" y2="182" stroke="var(--ed-fg-mute)" strokeWidth="1" />
        <path
          d="M40 100 C 70 100, 80 120, 110 120 S 170 62, 215 62 S 290 150, 330 150 S 395 70, 430 70 S 505 138, 545 138 S 600 58, 640 58 S 700 128, 740 128 S 850 100, 920 100"
          fill="none"
          stroke="var(--ed-accent)"
          strokeWidth="1.75"
          strokeLinecap="round"
        />
        <path
          d="M740 128 S 850 100, 920 100"
          fill="none"
          stroke="var(--ed-bg)"
          strokeWidth="4"
        />
        <path
          d="M740 128 S 850 100, 920 100"
          fill="none"
          stroke="var(--ed-accent)"
          strokeWidth="1.75"
          strokeDasharray="2 7"
          strokeLinecap="round"
        />
        {stops.map(([x, y, r]) => (
          <g key={x}>
            <circle cx={x} cy={y} r={r + 4} fill="var(--ed-bg)" />
            <circle cx={x} cy={y} r={r} fill="var(--ed-bg)" stroke="var(--ed-fg)" strokeWidth="1.5" />
          </g>
        ))}
        <circle cx="40" cy="100" r="6" fill="var(--ed-fg)" />
        <rect x="914" y="94" width="12" height="12" fill="var(--ed-accent)" />
      </svg>
      <div className="mt-1 flex justify-between font-mono-label">
        <span>First symptoms</span>
        <span>Confirmed diagnosis</span>
      </div>
      <figcaption className="mt-3 text-[0.8125rem] text-[var(--ed-fg-soft)]">
        Illustration of the shape of the problem, not data. Each open circle is a visit, test or referral.
      </figcaption>
    </figure>
  );
}

export function Lane({ who, children }: { who: string; children: React.ReactNode }) {
  return (
    <p className="font-mono-label mt-5 inline-block border border-border bg-[var(--ed-bg-elev)] px-2 py-1 normal-case tracking-[0.06em]">
      <span className="uppercase tracking-[0.18em]">{who}</span> {children}
    </p>
  );
}

const BAR_ROWS = [
  { label: "Documented disease ranked first", ours: 45.3, base: 35.4, oursN: "419 of 925", baseN: "327 of 925" },
  { label: "Documented disease in the top five", ours: 66.4, base: 57.6, oursN: "614 of 925", baseN: "533 of 925" },
] as const;

/** Measured result, drawn as two direct-labelled bar pairs. Values copied from eval/bars-resnik.md. */
export function MeasuredBars() {
  return (
    <figure className="ed-paper m-0 p-5 sm:p-7" data-testid="measured-bars">
      <p className="font-mono-label">Held-out public cases · 925 packets · 165 diseases</p>
      <div className="mt-5 space-y-8">
        {BAR_ROWS.map((row) => (
          <div key={row.label}>
            <p className="font-display text-lg text-[var(--ed-fg)]">{row.label}</p>
            {[
              { name: "Resnik best-match (shipped ranker)", v: row.ours, n: row.oursN, color: "var(--ed-accent)" },
              { name: "Simple baseline (term rarity)", v: row.base, n: row.baseN, color: "var(--ed-fg-mute)" },
            ].map((bar) => (
              <div key={bar.name} className="mt-2 grid grid-cols-[1fr_auto] items-center gap-3">
                <div>
                  <div className="text-[0.8125rem] text-[var(--ed-fg-soft)]">{bar.name}</div>
                  <div className="mt-1 h-3 w-full bg-[var(--ed-bg-soft)]" aria-hidden>
                    <div className="h-3" style={{ width: `${bar.v}%`, background: bar.color }} />
                  </div>
                </div>
                <div className="num text-right text-sm text-[var(--ed-fg)]">
                  <div className="text-lg font-medium">{bar.v.toFixed(1)}%</div>
                  <div className="text-xs text-muted-foreground">{bar.n}</div>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
      <figcaption className="mt-6 border-t border-border pt-4 text-[0.8125rem] leading-relaxed text-[var(--ed-fg-soft)]">
        Cases are curated from published reports (Phenopacket Store 0.1.27), not clinic notes. Only the 249 of 780
        diseases that map to a single Orphanet entry are scored. The split was fixed before scoring. This is a
        ranking test on public data. It says nothing about a real patient.
      </figcaption>
    </figure>
  );
}

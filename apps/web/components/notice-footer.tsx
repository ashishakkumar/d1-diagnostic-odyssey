"use client";

import { useEffect, useState } from "react";

const SHELL =
  "For research use only. Not for use in diagnostic procedures. Not a diagnosis and not for emergencies.";

export function NoticeFooter() {
  const [text, setText] = useState(SHELL);
  useEffect(() => {
    fetch("/api/footer")
      .then(async (response) => {
        if (!response.ok) {
          return;
        }
        const body = (await response.json()) as { text?: string };
        if (body.text) {
          setText(body.text);
        }
      })
      .catch(() => undefined);
  }, []);
  return (
    <footer className="mt-24 border-t border-border bg-[var(--ed-bg-soft)]">
      <div className="ed-shell py-8">
        <p className="font-mono-label">Read this first</p>
        <p className="mt-2 max-w-[62ch] text-[0.9375rem] leading-relaxed text-[var(--ed-fg-soft)]">{text}</p>
        <p className="mt-6 text-sm text-muted-foreground">
          A research prototype by{" "}
          <a className="underline hover:text-[var(--ed-accent)]" href="https://ashk.in">
            Ashish Kumar
          </a>
          . Synthetic data only. Nothing here has been used with a patient.
        </p>
      </div>
    </footer>
  );
}

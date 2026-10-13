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
    <footer className="border-t border-border px-4 py-4 text-sm text-muted-foreground">{text}</footer>
  );
}

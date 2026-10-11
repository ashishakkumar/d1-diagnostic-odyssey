"use client";

import { useState } from "react";

/** Signs in as a throwaway name, loads the first synthetic case, and opens its summary page. */
export function StartDemo({
  label = "Walk through a synthetic case",
  variant = "primary",
}: {
  label?: string;
  variant?: "primary" | "ghost";
}) {
  const [state, setState] = useState<"idle" | "busy" | "error">("idle");
  async function go() {
    setState("busy");
    try {
      const session = await fetch("/api/session", {
        method: "POST",
        credentials: "include",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name: "Visitor" }),
      });
      if (!session.ok) {
        throw new Error("session");
      }
      const loaded = await fetch("/api/demo/cases/separated/load", {
        method: "POST",
        credentials: "include",
      });
      if (!loaded.ok) {
        throw new Error("load");
      }
      const body = (await loaded.json()) as { case_id: string };
      window.location.assign(`/cases/${body.case_id}/summary`);
    } catch {
      setState("error");
    }
  }
  return (
    <span className="inline-flex flex-col gap-2">
      <button
        type="button"
        onClick={() => void go()}
        disabled={state === "busy"}
        className={`ed-btn ${variant === "primary" ? "ed-btn-primary" : "ed-btn-ghost"}`}
      >
        {state === "busy" ? "Opening…" : label}
        <span aria-hidden>→</span>
      </button>
      {state === "error" ? (
        <span role="alert" className="text-sm text-[var(--ed-accent)]">
          The demo could not be reached. Try again in a minute.
        </span>
      ) : null}
    </span>
  );
}

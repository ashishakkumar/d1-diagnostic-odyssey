"use client";

import { TimelineList, type TimelineEvent } from "@/components/timeline-list";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function TimelinePage() {
  const params = useParams<{ id: string }>();
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/cases/${params.id}/timeline`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("down");
        }
        return (await response.json()) as { events: TimelineEvent[] };
      })
      .then((body) => setEvents(body.events))
      .catch(() => setError("The notebook cannot reach the API."));
  }, [params.id]);

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <p className="font-mono-label">Step 1 · Record</p>
        <h1 className="font-display text-3xl italic md:text-4xl">Timeline</h1>
        <p className="max-w-[56ch] text-[var(--ed-fg-soft)]">Everything that has been accepted on this case, in order. Nothing appears here until a person accepts it.</p>
      </header>
      {error ? <p>{error}</p> : <TimelineList events={events} />}
    </section>
  );
}

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
    <section className="space-y-4">
      <h1 className="text-2xl">Timeline</h1>
      {error ? <p>{error}</p> : <TimelineList events={events} />}
    </section>
  );
}

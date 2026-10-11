import { WorkClient } from "@/components/work-client";
import { Suspense } from "react";

export default function WorkPage() {
  return (
    <Suspense fallback={<p className="font-ui">Reading the note.</p>}>
      <WorkClient />
    </Suspense>
  );
}

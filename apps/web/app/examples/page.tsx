import { NotebookHome } from "@/components/notebook-home";
import { Suspense } from "react";

export default function ExamplesPage() {
  return (
    <Suspense fallback={<p className="font-ui">Reading the note.</p>}>
      <NotebookHome />
    </Suspense>
  );
}

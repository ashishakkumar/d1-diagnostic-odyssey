import type { ReactNode } from "react";

export function Section({
  id,
  label,
  title,
  children,
}: {
  id?: string;
  label: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className="ed-shell scroll-mt-8 border-t border-border py-14 md:py-20">
      <p className="font-mono-label">{label}</p>
      <h2 className="font-display mt-3 max-w-[24ch] text-3xl italic leading-tight md:text-4xl">{title}</h2>
      <div className="mt-8">{children}</div>
    </section>
  );
}

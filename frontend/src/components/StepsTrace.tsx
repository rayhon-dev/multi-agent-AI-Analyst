"use client";

import { describeStep } from "@/lib/steps";

export function StepsTrace({ steps, live }: { steps: string[]; live: boolean }) {
  if (steps.length === 0) return null;

  return (
    <ol className="flex flex-col gap-1.5 pl-0.5">
      {steps.map((step, i) => {
        const { label, color, dot } = describeStep(step);
        const isLast = i === steps.length - 1;
        return (
          <li key={`${i}-${step}`} className="flex items-center gap-2 text-xs">
            <span className="relative flex h-1.5 w-1.5 shrink-0">
              {isLast && live && (
                <span className={`absolute inline-flex h-full w-full animate-ping rounded-full ${dot} opacity-75`} />
              )}
              <span className={`relative inline-flex h-1.5 w-1.5 rounded-full ${dot}`} />
            </span>
            <span className={color}>{label}</span>
          </li>
        );
      })}
    </ol>
  );
}

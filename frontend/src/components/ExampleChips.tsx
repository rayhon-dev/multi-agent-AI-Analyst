"use client";

const EXAMPLES = [
  "How many customers churned in 2024, and what does the FAQ say about why?",
  "What is Northwind Analytics' refund policy?",
  "What is the sum of the first 100 positive integers?",
];

export function ExampleChips({ onPick }: { onPick: (question: string) => void }) {
  return (
    <div className="flex flex-col items-center gap-4 px-4 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-950/40">
        <span className="text-2xl">✳</span>
      </div>
      <div>
        <h1 className="text-lg font-semibold text-neutral-100">Multi-Agent AI Analyst</h1>
        <p className="mt-1 max-w-md text-sm text-neutral-500">
          A supervisor routes your question to document retrieval, web search, SQL, and Python
          specialists, then a critic checks the answer before it comes back to you.
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-2 pt-2">
        {EXAMPLES.map((q) => (
          <button
            key={q}
            onClick={() => onPick(q)}
            className="rounded-full border border-neutral-800 bg-neutral-900 px-3.5 py-2 text-xs text-neutral-300 transition-colors hover:border-indigo-500/50 hover:bg-neutral-800 hover:text-white"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

export interface StepInfo {
  label: string;
  color: string;
  dot: string;
}

const ROUTE_LABELS: Record<string, string> = {
  retriever: "Routing to document retriever",
  web: "Routing to web search",
  data: "Routing to SQL agent",
  code: "Routing to code agent",
  finish: "Wrapping up",
};

export function describeStep(step: string): StepInfo {
  if (step.startsWith("memory(recall")) {
    return { label: step.replace("memory(recall ", "Recalled ").replace(")", ""), color: "text-slate-400", dot: "bg-slate-400" };
  }
  if (step === "memory(store)") {
    return { label: "Saved this turn to memory", color: "text-slate-400", dot: "bg-slate-400" };
  }
  if (step.startsWith("supervisor→")) {
    const target = step.replace("supervisor→", "");
    return { label: ROUTE_LABELS[target] ?? `Routing to ${target}`, color: "text-indigo-400", dot: "bg-indigo-400" };
  }
  if (step === "retriever") {
    return { label: "Searched company documents", color: "text-sky-400", dot: "bg-sky-400" };
  }
  if (step === "web") {
    return { label: "Searched the web", color: "text-teal-400", dot: "bg-teal-400" };
  }
  if (step.startsWith("web(skipped")) {
    return { label: "Web search skipped (no API key)", color: "text-slate-500", dot: "bg-slate-500" };
  }
  if (step === "data(sql)") {
    return { label: "Queried the database", color: "text-emerald-400", dot: "bg-emerald-400" };
  }
  if (step === "data(sql)-rejected") {
    return { label: "SQL query rejected (not read-only)", color: "text-red-400", dot: "bg-red-400" };
  }
  if (step === "data(sql)-error") {
    return { label: "SQL query errored", color: "text-red-400", dot: "bg-red-400" };
  }
  if (step === "code") {
    return { label: "Ran sandboxed Python", color: "text-orange-400", dot: "bg-orange-400" };
  }
  if (step === "generate") {
    return { label: "Drafted an answer", color: "text-violet-400", dot: "bg-violet-400" };
  }
  if (step.startsWith("critic→approved")) {
    return { label: "Critic approved the answer", color: "text-emerald-400", dot: "bg-emerald-400" };
  }
  if (step.startsWith("critic→revise")) {
    return { label: "Critic requested a revision", color: "text-amber-400", dot: "bg-amber-400" };
  }
  return { label: step, color: "text-slate-400", dot: "bg-slate-400" };
}

"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChevronDown, User, Sparkles } from "lucide-react";
import { StepsTrace } from "./StepsTrace";
import type { Message } from "@/lib/types";

export function ChatMessage({ message }: { message: Message }) {
  const [traceOpen, setTraceOpen] = useState(true);
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end gap-3">
        <div className="max-w-[75%] rounded-2xl rounded-br-sm bg-indigo-600 px-4 py-2.5 text-sm text-white shadow-lg shadow-indigo-950/40">
          {message.content}
        </div>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-neutral-800 text-neutral-400">
          <User size={16} />
        </div>
      </div>
    );
  }

  const hasAnswer = message.content.length > 0;
  const hasSteps = (message.steps?.length ?? 0) > 0;

  return (
    <div className="flex gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-950/40">
        <Sparkles size={16} />
      </div>
      <div className="flex max-w-[75%] flex-col gap-2">
        <div className="rounded-2xl rounded-bl-sm border border-neutral-800 bg-neutral-900/80 px-4 py-3 text-sm text-neutral-100 shadow-lg shadow-black/20 backdrop-blur">
          {hasSteps && (
            <div className="mb-2 border-b border-neutral-800 pb-2">
              <button
                onClick={() => setTraceOpen((v) => !v)}
                className="flex items-center gap-1 text-xs font-medium text-neutral-500 hover:text-neutral-300 transition-colors"
              >
                <ChevronDown
                  size={13}
                  className={`transition-transform ${traceOpen ? "rotate-0" : "-rotate-90"}`}
                />
                Agent trace &middot; {message.steps!.length} step{message.steps!.length === 1 ? "" : "s"}
              </button>
              {traceOpen && (
                <div className="mt-2">
                  <StepsTrace steps={message.steps!} live={message.streaming ?? false} />
                </div>
              )}
            </div>
          )}

          {hasAnswer ? (
            <div className="prose prose-sm prose-invert max-w-none prose-p:leading-relaxed prose-p:my-1.5 prose-ul:my-1.5 prose-li:my-0.5">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          ) : (
            message.streaming && (
              <div className="flex items-center gap-1.5 py-0.5 text-neutral-500">
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-neutral-500 [animation-delay:-0.3s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-neutral-500 [animation-delay:-0.15s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-neutral-500" />
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}

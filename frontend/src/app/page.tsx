"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, Loader2 } from "lucide-react";
import { ChatMessage } from "@/components/ChatMessage";
import { ExampleChips } from "@/components/ExampleChips";
import { streamChat } from "@/lib/api";
import type { Message } from "@/lib/types";

let idCounter = 0;
const nextId = () => `msg-${++idCounter}-${Date.now()}`;

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(question: string) {
    const trimmed = question.trim();
    if (!trimmed || busy) return;

    setError(null);
    setInput("");
    setBusy(true);

    const userMessage: Message = { id: nextId(), role: "user", content: trimmed };
    const assistantId = nextId();
    const assistantMessage: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      steps: [],
      streaming: true,
    };
    setMessages((prev) => [...prev, userMessage, assistantMessage]);

    try {
      await streamChat(trimmed, (event) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: event.answer, steps: event.steps, streaming: !event.done }
              : m
          )
        );
      });
    } catch {
      setError("Couldn't reach the backend. Is the API running?");
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, streaming: false } : m))
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-dvh flex-col bg-neutral-950">
      <header className="flex shrink-0 items-center justify-center border-b border-neutral-900 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-indigo-500 to-violet-600 text-xs text-white">
            ✳
          </div>
          <span className="text-sm font-medium text-neutral-300">Multi-Agent AI Analyst</span>
        </div>
      </header>

      <main className="flex flex-1 flex-col overflow-y-auto">
        <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-5 px-4 py-6">
          {messages.length === 0 ? (
            <div className="flex flex-1 items-center justify-center">
              <ExampleChips onPick={send} />
            </div>
          ) : (
            messages.map((m) => <ChatMessage key={m.id} message={m} />)
          )}
          <div ref={bottomRef} />
        </div>
      </main>

      <footer className="shrink-0 border-t border-neutral-900 bg-neutral-950/95 px-4 py-4 backdrop-blur">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="mx-auto flex w-full max-w-2xl items-end gap-2"
        >
          <div className="flex flex-1 items-center rounded-2xl border border-neutral-800 bg-neutral-900 px-4 py-2.5 transition-colors focus-within:border-indigo-500/60">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about customers, orders, docs, or run some Python..."
              disabled={busy}
              className="flex-1 bg-transparent text-sm text-neutral-100 outline-none placeholder:text-neutral-600 disabled:opacity-50"
            />
          </div>
          <button
            type="submit"
            disabled={busy || !input.trim()}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-indigo-600 text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-neutral-800 disabled:text-neutral-600"
          >
            {busy ? <Loader2 size={16} className="animate-spin" /> : <ArrowUp size={16} />}
          </button>
        </form>
        {error && <p className="mx-auto mt-2 max-w-2xl text-center text-xs text-red-400">{error}</p>}
      </footer>
    </div>
  );
}

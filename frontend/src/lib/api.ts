export interface ChatEvent {
  steps: string[];
  answer: string;
  done: boolean;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function streamChat(
  question: string,
  onEvent: (event: ChatEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    signal,
  });

  if (!res.ok || !res.body) {
    throw new Error(`Request failed with status ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let newlineIndex = buffer.indexOf("\n");
    while (newlineIndex !== -1) {
      const line = buffer.slice(0, newlineIndex).trim();
      buffer = buffer.slice(newlineIndex + 1);
      if (line) onEvent(JSON.parse(line) as ChatEvent);
      newlineIndex = buffer.indexOf("\n");
    }
  }

  const remainder = buffer.trim();
  if (remainder) onEvent(JSON.parse(remainder) as ChatEvent);
}

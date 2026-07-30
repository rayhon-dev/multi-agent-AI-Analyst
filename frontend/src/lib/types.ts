export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  steps?: string[];
  streaming?: boolean;
}

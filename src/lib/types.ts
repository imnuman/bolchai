export type MessageRole = "user" | "assistant" | "computer";

export type MessageType = "message" | "code" | "console" | "confirmation" | "error";

export type ConsoleFormat = "output" | "active_line" | "error";

export interface LMCMessage {
  role: MessageRole;
  type: MessageType;
  format?: string;
  content: string;
  start?: boolean;
  end?: boolean;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  type: MessageType;
  format?: string;
  content: string;
  streaming?: boolean;
}

export interface Settings {
  model: string;
  api_key: string;
  api_base: string;
  auto_run: boolean;
  custom_instructions: string;
  context_window: number;
  max_tokens: number;
  temperature: number;
}

export const DEFAULT_SETTINGS: Settings = {
  model: "gpt-4o",
  api_key: "",
  api_base: "",
  auto_run: false,
  custom_instructions: "",
  context_window: 128000,
  max_tokens: 4096,
  temperature: 0.0,
};

import { create } from "zustand";
import { ChatMessage, LMCMessage } from "../lib/types";

function generateId(): string {
  return Math.random().toString(36).substring(2, 10);
}

interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  awaitingConfirmation: boolean;
  pendingCode: { language: string; code: string } | null;

  addUserMessage: (content: string) => void;
  appendChunk: (chunk: LMCMessage) => void;
  confirmExecution: (approved: boolean) => void;
  clearMessages: () => void;
  setStreaming: (streaming: boolean) => void;
  setAwaitingConfirmation: (awaiting: boolean, code?: { language: string; code: string }) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  awaitingConfirmation: false,
  pendingCode: null,

  addUserMessage: (content: string) =>
    set((state) => ({
      messages: [
        ...state.messages,
        { id: generateId(), role: "user", type: "message", content },
      ],
    })),

  appendChunk: (chunk: LMCMessage) =>
    set((state) => {
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];

      if (chunk.start) {
        msgs.push({
          id: generateId(),
          role: chunk.role,
          type: chunk.type,
          format: chunk.format,
          content: chunk.content || "",
          streaming: true,
        });
        return { messages: msgs };
      }

      if (chunk.end && last && last.streaming) {
        const updated = { ...last, streaming: false };
        msgs[msgs.length - 1] = updated;
        return { messages: msgs };
      }

      if (last && last.streaming && last.role === chunk.role && last.type === chunk.type) {
        const updated = { ...last, content: last.content + (chunk.content || "") };
        msgs[msgs.length - 1] = updated;
        return { messages: msgs };
      }

      msgs.push({
        id: generateId(),
        role: chunk.role,
        type: chunk.type,
        format: chunk.format,
        content: chunk.content || "",
        streaming: false,
      });
      return { messages: msgs };
    }),

  confirmExecution: (_approved: boolean) =>
    set({ awaitingConfirmation: false, pendingCode: null }),

  clearMessages: () =>
    set({ messages: [], isStreaming: false, awaitingConfirmation: false, pendingCode: null }),

  setStreaming: (streaming: boolean) => set({ isStreaming: streaming }),

  setAwaitingConfirmation: (awaiting, code) =>
    set({ awaitingConfirmation: awaiting, pendingCode: code || null }),
}));

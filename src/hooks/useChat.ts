import { useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { useChatStore } from "../store/chatStore";
import { LMCMessage } from "../lib/types";

let unlisten: (() => void) | null = null;

export function useChat() {
  const store = useChatStore();

  const sendMessage = useCallback(async (content: string) => {
    store.addUserMessage(content);
    store.setStreaming(true);

    if (unlisten) unlisten();

    unlisten = await listen<LMCMessage>("chat-chunk", (event) => {
      const chunk = event.payload;

      if (chunk.type === "confirmation") {
        try {
          const codeData = JSON.parse(chunk.content);
          store.setAwaitingConfirmation(true, codeData);
        } catch {
          store.setAwaitingConfirmation(true, { language: "unknown", code: chunk.content });
        }
        return;
      }

      store.appendChunk(chunk);
    });

    try {
      await invoke("send_message", { message: content });
    } catch (err) {
      store.appendChunk({
        role: "computer",
        type: "error",
        content: String(err),
      });
    } finally {
      store.setStreaming(false);
    }
  }, [store]);

  const confirmExecution = useCallback(async (approved: boolean) => {
    store.confirmExecution(approved);
    try {
      await invoke("confirm_execution", { approved });
    } catch (err) {
      store.appendChunk({
        role: "computer",
        type: "error",
        content: String(err),
      });
    }
  }, [store]);

  const resetConversation = useCallback(async () => {
    store.clearMessages();
    try {
      await invoke("reset_conversation");
    } catch (_) {
      // ignore reset errors
    }
  }, [store]);

  return { sendMessage, confirmExecution, resetConversation };
}

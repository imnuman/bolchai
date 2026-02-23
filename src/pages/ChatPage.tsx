import { useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { useChatStore } from "../store/chatStore";
import { useChat } from "../hooks/useChat";
import MessageBubble from "../components/MessageBubble";
import InputBar from "../components/InputBar";
import ConfirmationPrompt from "../components/ConfirmationPrompt";

function ChatPage() {
  const { messages, isStreaming, awaitingConfirmation, pendingCode } = useChatStore();
  const { sendMessage, confirmExecution, resetConversation } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <header style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 20px",
        borderBottom: "1px solid var(--border)",
        background: "var(--bg-secondary)",
      }}>
        <h1 style={{ fontSize: "18px", fontWeight: 600 }}>Bolchai</h1>
        <div style={{ display: "flex", gap: "12px" }}>
          <button
            onClick={resetConversation}
            style={{
              background: "none",
              border: "1px solid var(--border)",
              color: "var(--text-secondary)",
              padding: "6px 12px",
              borderRadius: "6px",
              cursor: "pointer",
              fontSize: "13px",
            }}
          >
            New Chat
          </button>
          <Link
            to="/settings"
            style={{
              color: "var(--text-secondary)",
              textDecoration: "none",
              padding: "6px 12px",
              border: "1px solid var(--border)",
              borderRadius: "6px",
              fontSize: "13px",
            }}
          >
            Settings
          </Link>
        </div>
      </header>

      <main style={{ flex: 1, overflowY: "auto", padding: "20px" }}>
        {messages.length === 0 && (
          <div style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100%",
            color: "var(--text-secondary)",
          }}>
            <h2 style={{ fontSize: "24px", marginBottom: "8px" }}>Bolchai</h2>
            <p style={{ fontSize: "14px" }}>Type a message to start. I can write and run code for you.</p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {awaitingConfirmation && pendingCode && (
          <ConfirmationPrompt
            language={pendingCode.language}
            code={pendingCode.code}
            onConfirm={() => confirmExecution(true)}
            onDeny={() => confirmExecution(false)}
          />
        )}
        <div ref={bottomRef} />
      </main>

      <InputBar onSend={sendMessage} disabled={isStreaming || awaitingConfirmation} />
    </div>
  );
}

export default ChatPage;

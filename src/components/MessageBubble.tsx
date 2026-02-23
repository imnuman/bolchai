import ReactMarkdown from "react-markdown";
import { ChatMessage } from "../lib/types";
import CodeBlock from "./CodeBlock";
import OutputPanel from "./OutputPanel";

interface Props {
  message: ChatMessage;
}

function MessageBubble({ message }: Props) {
  if (message.type === "code") {
    return <CodeBlock language={message.format || "python"} code={message.content} />;
  }

  if (message.type === "console") {
    return <OutputPanel content={message.content} />;
  }

  if (message.type === "error") {
    return (
      <div style={{
        padding: "12px 16px",
        margin: "8px 0",
        background: "#2d1015",
        borderLeft: "3px solid var(--accent)",
        borderRadius: "6px",
        fontFamily: "monospace",
        fontSize: "13px",
        color: "#ff6b6b",
        whiteSpace: "pre-wrap",
      }}>
        {message.content}
      </div>
    );
  }

  const isUser = message.role === "user";

  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
      margin: "8px 0",
    }}>
      <div style={{
        maxWidth: "80%",
        padding: "12px 16px",
        borderRadius: "12px",
        background: isUser ? "var(--bg-input)" : "var(--bg-secondary)",
        border: `1px solid ${isUser ? "var(--border)" : "transparent"}`,
        fontSize: "14px",
        lineHeight: "1.6",
      }}>
        {message.streaming && !message.content && (
          <span style={{ color: "var(--text-secondary)", fontStyle: "italic" }}>Thinking...</span>
        )}
        <ReactMarkdown>{message.content}</ReactMarkdown>
      </div>
    </div>
  );
}

export default MessageBubble;

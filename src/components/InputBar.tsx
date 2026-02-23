import { useState, useRef, useEffect } from "react";

interface Props {
  onSend: (message: string) => void;
  disabled: boolean;
}

function InputBar({ onSend, disabled }: Props) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + "px";
    }
  }, [text]);

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div style={{
      padding: "12px 20px",
      borderTop: "1px solid var(--border)",
      background: "var(--bg-secondary)",
    }}>
      <div style={{
        display: "flex",
        gap: "10px",
        alignItems: "flex-end",
      }}>
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? "Waiting..." : "Type a message..."}
          disabled={disabled}
          rows={1}
          style={{
            flex: 1,
            padding: "10px 14px",
            background: "var(--bg-input)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            color: "var(--text-primary)",
            fontSize: "14px",
            resize: "none",
            outline: "none",
            lineHeight: "1.5",
            fontFamily: "inherit",
          }}
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !text.trim()}
          style={{
            padding: "10px 20px",
            background: disabled || !text.trim() ? "var(--border)" : "var(--accent)",
            color: "white",
            border: "none",
            borderRadius: "8px",
            cursor: disabled || !text.trim() ? "default" : "pointer",
            fontSize: "14px",
            fontWeight: 600,
            whiteSpace: "nowrap",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default InputBar;

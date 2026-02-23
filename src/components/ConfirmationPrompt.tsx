import CodeBlock from "./CodeBlock";

interface Props {
  language: string;
  code: string;
  onConfirm: () => void;
  onDeny: () => void;
}

function ConfirmationPrompt({ language, code, onConfirm, onDeny }: Props) {
  return (
    <div style={{
      margin: "12px 0",
      padding: "16px",
      background: "var(--bg-secondary)",
      border: "1px solid var(--warning)",
      borderRadius: "8px",
    }}>
      <p style={{ fontSize: "14px", marginBottom: "12px", color: "var(--warning)" }}>
        Run this code?
      </p>
      <CodeBlock language={language} code={code} />
      <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
        <button
          onClick={onConfirm}
          style={{
            padding: "8px 20px",
            background: "var(--success)",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontSize: "13px",
            fontWeight: 600,
          }}
        >
          Run
        </button>
        <button
          onClick={onDeny}
          style={{
            padding: "8px 20px",
            background: "none",
            color: "var(--text-secondary)",
            border: "1px solid var(--border)",
            borderRadius: "6px",
            cursor: "pointer",
            fontSize: "13px",
          }}
        >
          Skip
        </button>
      </div>
    </div>
  );
}

export default ConfirmationPrompt;

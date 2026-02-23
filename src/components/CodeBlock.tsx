import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

interface Props {
  language: string;
  code: string;
}

function CodeBlock({ language, code }: Props) {
  return (
    <div style={{ margin: "8px 0", borderRadius: "8px", overflow: "hidden", border: "1px solid var(--border)" }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "6px 12px",
        background: "#2d2d2d",
        fontSize: "12px",
        color: "var(--text-secondary)",
      }}>
        <span>{language}</span>
      </div>
      <SyntaxHighlighter
        language={language}
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          padding: "12px",
          fontSize: "13px",
          background: "var(--code-bg)",
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}

export default CodeBlock;

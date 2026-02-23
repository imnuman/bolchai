interface Props {
  content: string;
}

function OutputPanel({ content }: Props) {
  if (!content.trim()) return null;

  return (
    <div style={{
      margin: "4px 0",
      padding: "10px 14px",
      background: "#0d1117",
      borderLeft: "3px solid var(--success)",
      borderRadius: "4px",
      fontFamily: "'Cascadia Code', 'Fira Code', monospace",
      fontSize: "13px",
      lineHeight: "1.5",
      whiteSpace: "pre-wrap",
      wordBreak: "break-all",
      color: "#c9d1d9",
      maxHeight: "300px",
      overflowY: "auto",
    }}>
      {content}
    </div>
  );
}

export default OutputPanel;

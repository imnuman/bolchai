import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useSettings } from "../hooks/useSettings";
import { Settings, DEFAULT_SETTINGS } from "../lib/types";

function SettingsPage() {
  const { settings, updateSettings, loading } = useSettings();
  const [form, setForm] = useState<Settings>(DEFAULT_SETTINGS);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (settings) setForm(settings);
  }, [settings]);

  const handleSave = async () => {
    await updateSettings(form);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const fieldStyle: React.CSSProperties = {
    width: "100%",
    padding: "10px 12px",
    background: "var(--bg-input)",
    border: "1px solid var(--border)",
    borderRadius: "6px",
    color: "var(--text-primary)",
    fontSize: "14px",
    outline: "none",
  };

  const labelStyle: React.CSSProperties = {
    display: "block",
    marginBottom: "6px",
    fontSize: "13px",
    color: "var(--text-secondary)",
    fontWeight: 500,
  };

  if (loading) return <div style={{ padding: "40px", textAlign: "center" }}>Loading...</div>;

  return (
    <div style={{ maxWidth: "600px", margin: "0 auto", padding: "20px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "30px" }}>
        <Link to="/" style={{ color: "var(--text-secondary)", textDecoration: "none", fontSize: "20px" }}>
          &larr;
        </Link>
        <h1 style={{ fontSize: "20px" }}>Settings</h1>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <div>
          <label style={labelStyle}>Model</label>
          <input
            style={fieldStyle}
            value={form.model}
            onChange={(e) => setForm({ ...form, model: e.target.value })}
            placeholder="gpt-4o"
          />
        </div>

        <div>
          <label style={labelStyle}>API Key</label>
          <input
            style={fieldStyle}
            type="password"
            value={form.api_key}
            onChange={(e) => setForm({ ...form, api_key: e.target.value })}
            placeholder="sk-..."
          />
        </div>

        <div>
          <label style={labelStyle}>API Base URL (optional)</label>
          <input
            style={fieldStyle}
            value={form.api_base}
            onChange={(e) => setForm({ ...form, api_base: e.target.value })}
            placeholder="https://api.openai.com/v1"
          />
        </div>

        <div>
          <label style={labelStyle}>Temperature</label>
          <input
            style={{ ...fieldStyle, width: "100px" }}
            type="number"
            step="0.1"
            min="0"
            max="2"
            value={form.temperature}
            onChange={(e) => setForm({ ...form, temperature: parseFloat(e.target.value) })}
          />
        </div>

        <div>
          <label style={labelStyle}>Context Window</label>
          <input
            style={{ ...fieldStyle, width: "160px" }}
            type="number"
            value={form.context_window}
            onChange={(e) => setForm({ ...form, context_window: parseInt(e.target.value) })}
          />
        </div>

        <div>
          <label style={labelStyle}>Max Tokens</label>
          <input
            style={{ ...fieldStyle, width: "160px" }}
            type="number"
            value={form.max_tokens}
            onChange={(e) => setForm({ ...form, max_tokens: parseInt(e.target.value) })}
          />
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <input
            type="checkbox"
            checked={form.auto_run}
            onChange={(e) => setForm({ ...form, auto_run: e.target.checked })}
            style={{ width: "18px", height: "18px" }}
          />
          <label style={{ fontSize: "14px" }}>Auto-run code (skip confirmation)</label>
        </div>

        <div>
          <label style={labelStyle}>Custom Instructions</label>
          <textarea
            style={{ ...fieldStyle, minHeight: "80px", resize: "vertical" }}
            value={form.custom_instructions}
            onChange={(e) => setForm({ ...form, custom_instructions: e.target.value })}
            placeholder="Additional instructions for the AI..."
          />
        </div>

        <button
          onClick={handleSave}
          style={{
            padding: "12px 24px",
            background: saved ? "var(--success)" : "var(--accent)",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontSize: "14px",
            fontWeight: 600,
            alignSelf: "flex-start",
          }}
        >
          {saved ? "Saved!" : "Save Settings"}
        </button>
      </div>
    </div>
  );
}

export default SettingsPage;

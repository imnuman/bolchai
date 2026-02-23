import { useState, useEffect, useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Settings } from "../lib/types";

export function useSettings() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    invoke<Settings>("get_settings")
      .then(setSettings)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const updateSettings = useCallback(async (newSettings: Settings) => {
    await invoke("update_settings", { settings: newSettings });
    setSettings(newSettings);
  }, []);

  return { settings, updateSettings, loading };
}

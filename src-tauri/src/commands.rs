use crate::sidecar::SidecarManager;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tauri::{AppHandle, Emitter, State};
use tokio::sync::Mutex;

const BASE_URL: &str = "http://127.0.0.1:39821";

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LMCChunk {
    pub role: String,
    #[serde(rename = "type")]
    pub chunk_type: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub format: Option<String>,
    pub content: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub start: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub end: Option<bool>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Settings {
    pub model: String,
    pub api_key: String,
    pub api_base: String,
    pub auto_run: bool,
    pub custom_instructions: String,
    pub context_window: u32,
    pub max_tokens: u32,
    pub temperature: f32,
}

#[tauri::command]
pub async fn send_message(
    app: AppHandle,
    _sidecar: State<'_, Arc<Mutex<SidecarManager>>>,
    message: String,
) -> Result<(), String> {
    let client = reqwest::Client::new();
    let url = format!("{}/chat", BASE_URL);

    let resp = client
        .post(&url)
        .json(&serde_json::json!({ "message": message }))
        .send()
        .await
        .map_err(|e| format!("Failed to connect to sidecar: {}", e))?;

    if !resp.status().is_success() {
        return Err(format!("Sidecar returned status: {}", resp.status()));
    }

    // Read SSE stream
    let mut stream = resp.bytes_stream();
    use futures::StreamExt;

    let mut buffer = String::new();
    while let Some(chunk_result) = stream.next().await {
        let bytes = chunk_result.map_err(|e| e.to_string())?;
        buffer.push_str(&String::from_utf8_lossy(&bytes));

        // Process complete SSE events
        while let Some(pos) = buffer.find("\n\n") {
            let event_str = buffer[..pos].to_string();
            buffer = buffer[pos + 2..].to_string();

            for line in event_str.lines() {
                if let Some(data) = line.strip_prefix("data: ") {
                    if data == "[DONE]" {
                        return Ok(());
                    }
                    if let Ok(chunk) = serde_json::from_str::<LMCChunk>(data) {
                        let _ = app.emit("chat-chunk", &chunk);
                    }
                }
            }
        }
    }

    Ok(())
}

#[tauri::command]
pub async fn confirm_execution(
    _sidecar: State<'_, Arc<Mutex<SidecarManager>>>,
    approved: bool,
) -> Result<(), String> {
    let client = reqwest::Client::new();
    client
        .post(&format!("{}/confirm", BASE_URL))
        .json(&serde_json::json!({ "approved": approved }))
        .send()
        .await
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub async fn get_settings(
    _sidecar: State<'_, Arc<Mutex<SidecarManager>>>,
) -> Result<Settings, String> {
    let client = reqwest::Client::new();
    let resp = client
        .get(&format!("{}/settings", BASE_URL))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    resp.json::<Settings>()
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn update_settings(
    _sidecar: State<'_, Arc<Mutex<SidecarManager>>>,
    settings: Settings,
) -> Result<(), String> {
    let client = reqwest::Client::new();
    client
        .post(&format!("{}/settings", BASE_URL))
        .json(&settings)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub async fn reset_conversation(
    _sidecar: State<'_, Arc<Mutex<SidecarManager>>>,
) -> Result<(), String> {
    let client = reqwest::Client::new();
    client
        .post(&format!("{}/reset", BASE_URL))
        .send()
        .await
        .map_err(|e| e.to_string())?;
    Ok(())
}

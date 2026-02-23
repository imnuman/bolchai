mod commands;
mod config;
mod sidecar;

use sidecar::SidecarManager;
use std::sync::Arc;
use tauri::Manager;
use tokio::sync::Mutex;

pub fn run() {
    let sidecar = Arc::new(Mutex::new(SidecarManager::new()));

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(sidecar)
        .invoke_handler(tauri::generate_handler![
            commands::send_message,
            commands::confirm_execution,
            commands::get_settings,
            commands::update_settings,
            commands::reset_conversation,
        ])
        .setup(|app| {
            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                let state: tauri::State<'_, Arc<Mutex<SidecarManager>>> =
                    handle.state::<Arc<Mutex<SidecarManager>>>();
                let mut mgr: tokio::sync::MutexGuard<'_, SidecarManager> =
                    state.lock().await;
                if let Err(e) = mgr.start().await {
                    eprintln!("Failed to start sidecar: {}", e);
                }
            });
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                let handle = window.app_handle().clone();
                tauri::async_runtime::spawn(async move {
                    let state: tauri::State<'_, Arc<Mutex<SidecarManager>>> =
                        handle.state::<Arc<Mutex<SidecarManager>>>();
                    let mut mgr: tokio::sync::MutexGuard<'_, SidecarManager> =
                        state.lock().await;
                    mgr.stop();
                });
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

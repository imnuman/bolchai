use std::process::{Child, Command};
use std::time::Duration;

const SIDECAR_PORT: u16 = 39821;
const HEALTH_URL: &str = "http://127.0.0.1:39821/health";

enum SidecarMode {
    Bundled(String),
    Python { interpreter: String, script: String },
}

pub struct SidecarManager {
    process: Option<Child>,
}

impl SidecarManager {
    pub fn new() -> Self {
        Self { process: None }
    }

    pub async fn start(&mut self) -> Result<(), String> {
        let mode = Self::find_sidecar()?;

        let child = match &mode {
            SidecarMode::Bundled(path) => {
                Command::new(path)
                    .arg("--port")
                    .arg(SIDECAR_PORT.to_string())
                    .spawn()
            }
            SidecarMode::Python { interpreter, script } => {
                Command::new(interpreter)
                    .arg(script)
                    .arg("--port")
                    .arg(SIDECAR_PORT.to_string())
                    .spawn()
            }
        }
        .map_err(|e| format!("Failed to spawn sidecar: {}", e))?;

        self.process = Some(child);

        // Poll /health until ready (up to 30 seconds)
        let client = reqwest::Client::new();
        for _ in 0..60 {
            tokio::time::sleep(Duration::from_millis(500)).await;
            if let Ok(resp) = client.get(HEALTH_URL).send().await {
                if resp.status().is_success() {
                    println!("Sidecar is ready on port {}", SIDECAR_PORT);
                    return Ok(());
                }
            }
        }

        Err("Sidecar failed to become healthy within 30 seconds".into())
    }

    pub fn stop(&mut self) {
        if let Some(ref mut child) = self.process {
            let _ = child.kill();
            let _ = child.wait();
        }
        self.process = None;
    }

    fn find_sidecar() -> Result<SidecarMode, String> {
        // Check if we have a bundled binary (production)
        let exe_dir = std::env::current_exe()
            .map(|p| p.parent().unwrap_or(std::path::Path::new(".")).to_path_buf())
            .unwrap_or_default();

        for name in &["bolchai-engine", "bolchai-engine.exe"] {
            let bundled = exe_dir.join("sidecar").join(name);
            if bundled.exists() {
                return Ok(SidecarMode::Bundled(
                    bundled.to_string_lossy().into_owned(),
                ));
            }
        }

        // Development mode: find python and the script
        let script = Self::find_sidecar_main()?;

        for py in &["python3.12", "python3", "python"] {
            if let Ok(output) = Command::new(py).arg("--version").output() {
                if output.status.success() {
                    return Ok(SidecarMode::Python {
                        interpreter: py.to_string(),
                        script,
                    });
                }
            }
        }

        Err("No Python interpreter or bundled sidecar found".into())
    }

    fn find_sidecar_main() -> Result<String, String> {
        let candidates = [
            "../sidecar/main.py",
            "../../sidecar/main.py",
            "sidecar/main.py",
        ];

        for candidate in &candidates {
            let path = std::path::Path::new(candidate);
            if path.exists() {
                return Ok(
                    path.canonicalize()
                        .map_err(|e| e.to_string())?
                        .to_string_lossy()
                        .into_owned(),
                );
            }
        }

        Err("Could not find sidecar/main.py".into())
    }
}

impl Drop for SidecarManager {
    fn drop(&mut self) {
        self.stop();
    }
}

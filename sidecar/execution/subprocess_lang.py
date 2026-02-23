import os
import subprocess
import traceback

from .base import BaseLanguage


class PowerShellLanguage(BaseLanguage):
    name = "PowerShell"
    aliases = ["powershell", "ps1", "pwsh"]
    file_extension = "ps1"

    def run(self, code):
        yield from _run_subprocess(["powershell", "-Command", code])

    def stop(self):
        pass


class ShellLanguage(BaseLanguage):
    name = "Shell"
    aliases = ["shell", "bash", "sh", "cmd", "bat", "batch"]
    file_extension = "sh"

    def run(self, code):
        if os.name == "nt":
            yield from _run_subprocess(["cmd", "/c", code])
        else:
            yield from _run_subprocess(["bash", "-c", code])

    def stop(self):
        pass


def _run_subprocess(cmd):
    """Run a subprocess command and yield output chunks."""
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in iter(proc.stdout.readline, ""):
            yield {
                "type": "console",
                "format": "output",
                "content": line,
            }
        proc.wait()
        if proc.returncode != 0:
            yield {
                "type": "console",
                "format": "output",
                "content": f"\n[Process exited with code {proc.returncode}]",
            }
    except Exception:
        yield {
            "type": "console",
            "format": "output",
            "content": traceback.format_exc(),
        }

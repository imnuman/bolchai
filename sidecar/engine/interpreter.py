import threading

from config import BolchaiSettings
from .llm import LLMWrapper
from .respond import respond
from execution.python_kernel import PythonKernel
from execution.subprocess_lang import PowerShellLanguage, ShellLanguage


class BolchaiInterpreter:
    def __init__(self, settings: BolchaiSettings):
        self.settings = settings
        self.messages = []
        self.llm = LLMWrapper(settings)

        # Code execution engines
        self._languages = {}
        self._init_languages()

        # Confirmation flow
        self._confirm_event = threading.Event()
        self._confirm_result = False

    def _init_languages(self):
        """Initialize language executors lazily."""
        # We don't start them until first use to save resources
        self._language_classes = {
            "python": PythonKernel,
            "py": PythonKernel,
            "python3": PythonKernel,
            "powershell": PowerShellLanguage,
            "ps1": PowerShellLanguage,
            "pwsh": PowerShellLanguage,
            "shell": ShellLanguage,
            "bash": ShellLanguage,
            "sh": ShellLanguage,
            "cmd": ShellLanguage,
            "bat": ShellLanguage,
            "batch": ShellLanguage,
        }

    def get_language(self, name):
        """Get a language executor, creating it if needed."""
        name = name.lower().strip()
        if name not in self._language_classes:
            return None

        if name not in self._languages:
            cls = self._language_classes[name]
            # Share instances between aliases
            for alias, existing in self._languages.items():
                if isinstance(existing, cls):
                    self._languages[name] = existing
                    return existing
            self._languages[name] = cls()

        return self._languages[name]

    def run_code(self, language, code):
        """Execute code in the given language. Yields output chunks."""
        executor = self.get_language(language)
        if executor is None:
            yield {
                "type": "console",
                "format": "output",
                "content": f"Language '{language}' is not supported.",
            }
            return

        output_parts = []
        for chunk in executor.run(code):
            output_parts.append(chunk)
            yield chunk

        # Collect output and add to messages
        output_text = ""
        for part in output_parts:
            if part.get("type") == "console" and part.get("format") == "output":
                output_text += part.get("content", "")

        # Truncate output if too long
        max_output = 5000
        if len(output_text) > max_output:
            output_text = (
                output_text[:max_output]
                + f"\n\n[Output truncated to {max_output} characters]"
            )

        self.messages.append({
            "role": "computer",
            "type": "console",
            "format": "output",
            "content": output_text,
        })

    def chat(self, message):
        """
        Main entry point. Takes a user message, yields LMC chunks.
        """
        self.messages.append({
            "role": "user",
            "type": "message",
            "content": message,
        })

        # Track current assistant message being built
        current_assistant_msg = None

        for chunk in respond(self):
            yield chunk

            # Accumulate assistant messages
            if chunk.get("role") == "assistant":
                if chunk.get("type") == "message":
                    if current_assistant_msg is None or current_assistant_msg["type"] != "message":
                        if current_assistant_msg is not None:
                            self.messages.append(current_assistant_msg)
                        current_assistant_msg = {
                            "role": "assistant",
                            "type": "message",
                            "content": chunk.get("content", ""),
                        }
                    else:
                        current_assistant_msg["content"] += chunk.get("content", "")
                elif chunk.get("type") == "code":
                    if current_assistant_msg is not None and current_assistant_msg["type"] != "code":
                        self.messages.append(current_assistant_msg)
                        current_assistant_msg = {
                            "role": "assistant",
                            "type": "code",
                            "format": chunk.get("format", "python"),
                            "content": chunk.get("content", ""),
                        }
                    elif current_assistant_msg is None:
                        current_assistant_msg = {
                            "role": "assistant",
                            "type": "code",
                            "format": chunk.get("format", "python"),
                            "content": chunk.get("content", ""),
                        }
                    else:
                        current_assistant_msg["content"] += chunk.get("content", "")

        # Append last assistant message
        if current_assistant_msg is not None:
            self.messages.append(current_assistant_msg)

    def confirm(self, approved):
        """Called from the API when user confirms/denies code execution."""
        self._confirm_result = approved
        self._confirm_event.set()

    def wait_for_confirmation(self, timeout=300):
        """Block until user confirms or denies. Returns True/False."""
        self._confirm_event.clear()
        self._confirm_result = False
        self._confirm_event.wait(timeout=timeout)
        return self._confirm_result

    def reset(self):
        """Clear conversation history."""
        self.messages = []

    def update_settings(self, settings: BolchaiSettings):
        """Update settings and propagate to LLM."""
        self.settings = settings
        self.llm.update_settings(settings)

    def cleanup(self):
        """Clean up all resources."""
        for lang in self._languages.values():
            try:
                lang.terminate()
            except Exception:
                pass

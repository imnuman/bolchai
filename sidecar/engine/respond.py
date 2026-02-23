import json
import traceback


def respond(interpreter):
    """
    Core respond loop. Yields LMC chunks.
    Calls LLM, detects code, executes, feeds output back, loops until done.
    """
    from .system_message import build_system_message

    while True:
        # Build system message
        system_message = build_system_message(interpreter.settings.custom_instructions)

        rendered_system_message = {
            "role": "system",
            "type": "message",
            "content": system_message,
        }

        # Create messages for LLM
        messages_for_llm = [rendered_system_message] + interpreter.messages.copy()

        # Must have at least one user message
        if len(interpreter.messages) == 0:
            break

        # If last message is not code, call LLM
        if interpreter.messages[-1]["type"] != "code":
            try:
                for chunk in interpreter.llm.run(messages_for_llm):
                    yield {"role": "assistant", **chunk}
            except Exception as e:
                error_msg = str(e)
                if "auth" in error_msg.lower() or "api key" in error_msg.lower():
                    yield {
                        "role": "computer",
                        "type": "error",
                        "content": f"Authentication error: {error_msg}\n\nPlease check your API key in Settings.",
                    }
                else:
                    yield {
                        "role": "computer",
                        "type": "error",
                        "content": f"LLM Error: {error_msg}",
                    }
                break

        # Check if we have code to run
        if interpreter.messages[-1]["type"] == "code":
            language = interpreter.messages[-1].get("format", "python").lower().strip()
            code = interpreter.messages[-1]["content"]

            # Clean up common hallucinations
            if code.startswith("`\n"):
                code = code[2:].strip()
                interpreter.messages[-1]["content"] = code

            # Handle JSON-wrapped code
            clean = code.replace("\n", "").replace(" ", "")
            if clean.startswith('{"language":'):
                try:
                    code_dict = json.loads(code)
                    if set(code_dict.keys()) == {"language", "code"}:
                        language = code_dict["language"]
                        code = code_dict["code"]
                        interpreter.messages[-1]["content"] = code
                        interpreter.messages[-1]["format"] = language
                except Exception:
                    pass

            # Skip text/markdown code blocks (LLM taking notes)
            if language in ("text", "markdown", "plaintext"):
                interpreter.messages[-1] = {
                    "role": "assistant",
                    "type": "message",
                    "content": f"```\n{code}\n```",
                }
                continue

            # Check if language is supported
            if not interpreter.get_language(language):
                yield {
                    "role": "computer",
                    "type": "console",
                    "format": "output",
                    "content": f"`{language}` is not supported. Available: python, powershell, shell",
                }
                break

            # Skip empty code
            if not code.strip():
                yield {
                    "role": "computer",
                    "type": "console",
                    "format": "output",
                    "content": "Code block was empty.",
                }
                continue

            # Yield confirmation request (unless auto_run is on)
            if not interpreter.settings.auto_run:
                yield {
                    "role": "computer",
                    "type": "confirmation",
                    "format": "execution",
                    "content": json.dumps({
                        "type": "code",
                        "format": language,
                        "content": code,
                    }),
                }

                # Wait for user confirmation
                approved = interpreter.wait_for_confirmation()
                if not approved:
                    yield {
                        "role": "computer",
                        "type": "console",
                        "format": "output",
                        "content": "Code execution skipped by user.",
                    }
                    break

            # Execute code
            try:
                for line in interpreter.run_code(language, code):
                    yield {"role": "computer", **line}
            except Exception:
                yield {
                    "role": "computer",
                    "type": "console",
                    "format": "output",
                    "content": traceback.format_exc(),
                }

        else:
            # LLM didn't produce code, check if we should loop
            if (
                interpreter.messages
                and interpreter.messages[-1].get("role") == "assistant"
            ):
                # Done — LLM chose not to write code
                break

            break

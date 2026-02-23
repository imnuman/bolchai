import os

os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"

import litellm
litellm.suppress_debug_info = True
litellm.REPEATED_STREAMING_CHUNK_LIMIT = 99999999

import tokentrim as tt

from .utils import merge_deltas, parse_partial_json, convert_to_openai_messages

# Tool schema for function-calling models
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute",
        "description": "Executes code on the user's machine and returns the output",
        "parameters": {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "description": "The programming language",
                    "enum": ["python", "powershell", "shell"],
                },
                "code": {
                    "type": "string",
                    "description": "The code to execute",
                },
            },
            "required": ["language", "code"],
        },
    },
}

EXECUTION_INSTRUCTIONS = (
    "To execute code on the user's machine, write a markdown code block. "
    "Specify the language after the ```. You will receive the output. "
    "Use any programming language."
)


class LLMWrapper:
    def __init__(self, settings):
        self.model = settings.model
        self.temperature = settings.temperature
        self.context_window = settings.context_window
        self.max_tokens = settings.max_tokens
        self.api_key = settings.api_key
        self.api_base = settings.api_base
        self.supports_functions = None

    def update_settings(self, settings):
        self.model = settings.model
        self.temperature = settings.temperature
        self.context_window = settings.context_window
        self.max_tokens = settings.max_tokens
        self.api_key = settings.api_key
        self.api_base = settings.api_base
        self.supports_functions = None

    def run(self, messages):
        """
        Takes LMC messages, converts to OpenAI format, calls LLM, yields LMC chunks.
        """
        if self.supports_functions is None:
            try:
                self.supports_functions = litellm.supports_function_calling(self.model)
            except Exception:
                self.supports_functions = False

        # Convert LMC messages to OpenAI format
        openai_messages = convert_to_openai_messages(
            messages, function_calling=self.supports_functions
        )

        system_message = openai_messages[0]["content"]
        chat_messages = openai_messages[1:]

        # Trim messages to fit context window
        try:
            trim_to = self.context_window - self.max_tokens - 25
            chat_messages = tt.trim(
                chat_messages,
                system_message=system_message,
                max_tokens=trim_to,
            )
        except Exception:
            try:
                chat_messages = tt.trim(
                    chat_messages,
                    system_message=system_message,
                    model=self.model,
                )
            except Exception:
                chat_messages = tt.trim(
                    chat_messages,
                    system_message=system_message,
                    max_tokens=8000,
                )

        # Ensure system message is first
        if not chat_messages or chat_messages[0].get("role") != "system":
            chat_messages = [{"role": "system", "content": system_message}] + chat_messages

        # Build request params
        params = {
            "model": self.model,
            "messages": chat_messages,
            "stream": True,
        }

        if self.api_key:
            params["api_key"] = self.api_key
        if self.api_base:
            params["api_base"] = self.api_base
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        if self.temperature is not None:
            params["temperature"] = self.temperature

        if self.supports_functions:
            params["tools"] = [TOOL_SCHEMA]
            # Process messages for tool calling format
            chat_messages = _process_messages_for_tools(chat_messages)
            params["messages"] = chat_messages
            yield from _run_tool_calling_llm(params)
        else:
            # Add execution instructions for text-based models
            if chat_messages and chat_messages[0]["role"] == "system":
                chat_messages[0]["content"] += "\n" + EXECUTION_INSTRUCTIONS
                params["messages"] = chat_messages
            yield from _run_text_llm(params)


def _process_messages_for_tools(messages):
    """Convert function_call format to tool_calls format."""
    processed = []
    last_tool_id = 0

    i = 0
    while i < len(messages):
        message = messages[i]

        if message.get("function_call"):
            last_tool_id += 1
            tool_id = f"toolu_{last_tool_id}"
            msg = dict(message)
            function = msg.pop("function_call")
            msg["tool_calls"] = [
                {"id": tool_id, "type": "function", "function": function}
            ]
            processed.append(msg)

            if i + 1 < len(messages) and messages[i + 1].get("role") == "function":
                next_msg = dict(messages[i + 1])
                next_msg["role"] = "tool"
                next_msg["tool_call_id"] = tool_id
                processed.append(next_msg)
                i += 1
            else:
                processed.append(
                    {"role": "tool", "tool_call_id": tool_id, "content": ""}
                )
        elif message.get("role") == "function":
            last_tool_id += 1
            tool_id = f"toolu_{last_tool_id}"
            processed.append({
                "role": "assistant",
                "tool_calls": [{
                    "id": tool_id,
                    "type": "function",
                    "function": {
                        "name": "execute",
                        "arguments": "{}",
                    },
                }],
            })
            msg = dict(message)
            msg["role"] = "tool"
            msg["tool_call_id"] = tool_id
            processed.append(msg)
        else:
            processed.append(message)

        i += 1

    return processed


def _run_tool_calling_llm(params):
    """Parse tool-calling LLM output into LMC chunks."""
    accumulated_deltas = {}
    language = None
    code = ""

    for chunk in litellm.completion(**params):
        if "choices" not in chunk or len(chunk["choices"]) == 0:
            continue

        delta = chunk["choices"][0]["delta"]

        if "tool_calls" in delta and delta["tool_calls"]:
            if len(delta["tool_calls"]) > 0 and delta["tool_calls"][0].function:
                delta = {
                    "function_call": {
                        "name": delta["tool_calls"][0].function.name,
                        "arguments": delta["tool_calls"][0].function.arguments,
                    }
                }

        accumulated_deltas = merge_deltas(accumulated_deltas, delta)

        if "content" in delta and delta["content"]:
            yield {"type": "message", "content": delta["content"]}

        if (
            accumulated_deltas.get("function_call")
            and "arguments" in accumulated_deltas["function_call"]
            and accumulated_deltas["function_call"]["arguments"]
        ):
            arguments = parse_partial_json(
                accumulated_deltas["function_call"]["arguments"]
            )
            if arguments:
                if (
                    language is None
                    and "language" in arguments
                    and "code" in arguments
                    and arguments["language"]
                ):
                    language = arguments["language"]

                if language is not None and "code" in arguments:
                    code_delta = arguments["code"][len(code):]
                    code = arguments["code"]
                    if code_delta:
                        yield {
                            "type": "code",
                            "format": language,
                            "content": code_delta,
                        }


def _run_text_llm(params):
    """Parse text-based LLM output, detecting code blocks via triple backticks."""
    inside_code_block = False
    accumulated_block = ""
    language = None

    for chunk in litellm.completion(**params):
        if "choices" not in chunk or len(chunk["choices"]) == 0:
            continue

        content = chunk["choices"][0]["delta"].get("content", "")
        if content is None:
            continue

        accumulated_block += content

        if accumulated_block.endswith("`"):
            continue

        # Entering a code block
        if "```" in accumulated_block and not inside_code_block:
            inside_code_block = True
            accumulated_block = accumulated_block.split("```")[1]

        # Exiting a code block
        if inside_code_block and "```" in accumulated_block:
            return

        if inside_code_block:
            if language is None and "\n" in accumulated_block:
                language = accumulated_block.split("\n")[0]
                if language == "":
                    language = "python"
                else:
                    language = "".join(c for c in language if c.isalpha())

            if language:
                yield {
                    "type": "code",
                    "format": language,
                    "content": content.replace(language, ""),
                }
        else:
            yield {"type": "message", "content": content}

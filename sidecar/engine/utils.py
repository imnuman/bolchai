import json


def merge_deltas(original, delta):
    """
    Pushes the delta into the original and returns that.
    Reconstructs OpenAI streaming responses into complete message objects.
    """
    for key, value in dict(delta).items():
        if value is not None:
            if isinstance(value, str):
                if key in original:
                    original[key] = (original[key] or "") + (value or "")
                else:
                    original[key] = value
            else:
                value = dict(value)
                if key not in original:
                    original[key] = value
                else:
                    merge_deltas(original[key], value)
    return original


def parse_partial_json(s):
    """
    Parses incomplete/malformed JSON from streaming LLM responses.
    """
    try:
        return json.loads(s)
    except Exception:
        pass

    new_s = ""
    stack = []
    is_inside_string = False
    escaped = False

    for char in s:
        if is_inside_string:
            if char == '"' and not escaped:
                is_inside_string = False
            elif char == "\n" and not escaped:
                char = "\\n"
            elif char == "\\":
                escaped = not escaped
            else:
                escaped = False
        else:
            if char == '"':
                is_inside_string = True
                escaped = False
            elif char == "{":
                stack.append("}")
            elif char == "[":
                stack.append("]")
            elif char == "}" or char == "]":
                if stack and stack[-1] == char:
                    stack.pop()
                else:
                    return None

        new_s += char

    if is_inside_string:
        new_s += '"'

    for closing_char in reversed(stack):
        new_s += closing_char

    try:
        return json.loads(new_s)
    except Exception:
        return None


def convert_to_openai_messages(messages, function_calling=True):
    """
    Converts LMC messages into OpenAI API compatible messages.
    Simplified version — no vision, no image handling.
    """
    new_messages = []

    for message in messages:
        new_message = {}

        if message["type"] == "message":
            new_message["role"] = message["role"]
            new_message["content"] = message["content"]

        elif message["type"] == "code":
            new_message["role"] = "assistant"
            if function_calling:
                new_message["function_call"] = {
                    "name": "execute",
                    "arguments": json.dumps(
                        {"language": message["format"], "code": message["content"]}
                    ),
                }
                new_message["content"] = ""
            else:
                new_message["content"] = (
                    f"```{message['format']}\n{message['content']}\n```"
                )

        elif message["type"] == "console" and message.get("format") == "output":
            if function_calling:
                new_message["role"] = "function"
                new_message["name"] = "execute"
                content = message.get("content", "")
                if not isinstance(content, str):
                    content = str(content)
                new_message["content"] = content if content.strip() else "No output"
            else:
                new_message["role"] = "user"
                content = message.get("content", "")
                if content.strip():
                    new_message["content"] = f"Code output:\n```\n{content}\n```"
                else:
                    new_message["content"] = "Code executed successfully (no output)."

        elif message["type"] == "error":
            continue

        else:
            continue

        if isinstance(new_message.get("content"), str):
            new_message["content"] = new_message["content"].strip()

        if new_message:
            new_messages.append(new_message)

    # For non-function-calling models, combine adjacent same-role messages
    if not function_calling:
        combined = []
        for msg in new_messages:
            if combined and combined[-1]["role"] == msg["role"] and isinstance(msg.get("content"), str):
                combined[-1]["content"] += "\n" + msg["content"]
            else:
                combined.append(msg)
        new_messages = combined

    return new_messages

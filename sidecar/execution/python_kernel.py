import os
import queue
import re
import sys
import threading
import time
import traceback

from .base import BaseLanguage

# PyInstaller guard: when running from an executable, ipykernel calls itself
if "ipykernel_launcher" in sys.argv:
    if sys.path[0] == "":
        del sys.path[0]
    from ipykernel import kernelapp as app
    app.launch_new_instance()
    sys.exit(0)


class PythonKernel(BaseLanguage):
    name = "Python"
    aliases = ["py", "python", "python3"]
    file_extension = "py"

    def __init__(self):
        from jupyter_client import KernelManager

        self.km = KernelManager(kernel_name="python3")
        self.km.start_kernel()
        self.kc = self.km.client()
        self.kc.start_channels()

        while not self.kc.is_alive():
            time.sleep(0.1)
        time.sleep(0.5)

        self.listener_thread = None
        self.finish_flag = False

        # Set up matplotlib inline
        for _ in self.run("%matplotlib inline\nimport matplotlib.pyplot as plt"):
            pass

    def terminate(self):
        try:
            self.kc.stop_channels()
            self.km.shutdown_kernel()
        except Exception:
            pass

    def run(self, code):
        while not self.kc.is_alive():
            time.sleep(0.1)

        self.finish_flag = False
        try:
            message_queue = queue.Queue()
            self._execute_code(code, message_queue)
            yield from self._capture_output(message_queue)
        except GeneratorExit:
            raise
        except Exception:
            yield {"type": "console", "format": "output", "content": traceback.format_exc()}

    def _execute_code(self, code, message_queue):
        def iopub_listener():
            while True:
                if self.finish_flag:
                    self.km.interrupt_kernel()
                    return
                try:
                    msg = self.kc.iopub_channel.get_msg(timeout=0.05)
                except queue.Empty:
                    continue
                except Exception:
                    continue

                if (
                    msg["header"]["msg_type"] == "status"
                    and msg["content"]["execution_state"] == "idle"
                ):
                    self.finish_flag = True
                    return

                content = msg["content"]

                if msg["msg_type"] == "stream":
                    message_queue.put({
                        "type": "console",
                        "format": "output",
                        "content": content["text"],
                    })
                elif msg["msg_type"] == "error":
                    tb = "\n".join(content["traceback"])
                    ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
                    tb = ansi_escape.sub("", tb)
                    message_queue.put({
                        "type": "console",
                        "format": "output",
                        "content": tb,
                    })
                elif msg["msg_type"] in ["display_data", "execute_result"]:
                    data = content["data"]
                    if "image/png" in data:
                        message_queue.put({
                            "type": "image",
                            "format": "base64.png",
                            "content": data["image/png"],
                        })
                    elif "text/html" in data:
                        message_queue.put({
                            "type": "console",
                            "format": "output",
                            "content": data["text/html"],
                        })
                    elif "text/plain" in data:
                        message_queue.put({
                            "type": "console",
                            "format": "output",
                            "content": data["text/plain"],
                        })

        self.listener_thread = threading.Thread(target=iopub_listener)
        self.listener_thread.start()
        self.kc.execute(code)

    def _capture_output(self, message_queue):
        while True:
            time.sleep(0.05)
            try:
                output = message_queue.get(timeout=0.1)
                yield output
            except queue.Empty:
                if self.finish_flag:
                    time.sleep(0.1)
                    try:
                        output = message_queue.get(timeout=0.1)
                        yield output
                    except queue.Empty:
                        break

    def stop(self):
        self.finish_flag = True

import asyncio
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from config import BolchaiSettings
from engine.interpreter import BolchaiInterpreter


executor = ThreadPoolExecutor(max_workers=2)


def create_app() -> FastAPI:
    app = FastAPI(title="Bolchai Engine")
    settings = BolchaiSettings.load()
    interpreter = BolchaiInterpreter(settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/chat")
    async def chat(request: Request):
        body = await request.json()
        message = body.get("message", "")

        async def event_generator():
            loop = asyncio.get_event_loop()
            queue: asyncio.Queue = asyncio.Queue()
            stop_event = threading.Event()

            def run_interpreter():
                try:
                    for chunk in interpreter.chat(message):
                        asyncio.run_coroutine_threadsafe(
                            queue.put(chunk), loop
                        )
                except Exception as e:
                    asyncio.run_coroutine_threadsafe(
                        queue.put({
                            "role": "computer",
                            "type": "error",
                            "content": str(e),
                        }),
                        loop,
                    )
                finally:
                    stop_event.set()
                    asyncio.run_coroutine_threadsafe(queue.put(None), loop)

            loop.run_in_executor(executor, run_interpreter)

            while True:
                chunk = await queue.get()
                if chunk is None:
                    yield {"data": "[DONE]"}
                    break
                yield {"data": json.dumps(chunk)}

        return EventSourceResponse(event_generator())

    @app.post("/confirm")
    async def confirm(request: Request):
        body = await request.json()
        approved = body.get("approved", False)
        interpreter.confirm(approved)
        return {"status": "ok"}

    @app.get("/settings")
    async def get_settings():
        return interpreter.settings.model_dump()

    @app.post("/settings")
    async def update_settings(request: Request):
        body = await request.json()
        new_settings = BolchaiSettings(**body)
        new_settings.save()
        interpreter.update_settings(new_settings)
        return {"status": "ok"}

    @app.post("/reset")
    async def reset():
        interpreter.reset()
        return {"status": "ok"}

    return app

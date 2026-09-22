from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    user_message = await request.body()
    print(user_message)

    return {
        "id": "mock-chatcmpl-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "mock-model",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": (
                        f"mock-model"
                        f"Mock response to: {user_message}"
                    ),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 10,
            "total_tokens": 20,
        },
    }

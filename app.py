from fastapi import FastAPI, Request
from pydantic import BaseModel
import json

app = FastAPI()


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    user_message = (await request.body()).decode("utf-8")
    payload = json.loads(user_message)
    print(type(payload))

    tools = payload.get("tools", [])
    has_search = any(
        tool.get("function", {}).get("name") == "internet_search"
        for tool in tools
    )
  
    if payload["messages"][-1]["role"]=="user" and payload["messages"][-1]["content"]=="call tool" and has_search:
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
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_mock_123",
                                "type": "function",
                                "function": {
                                    "name": "internet_search",
                                    "arguments": json.dumps({"query": "who is macron?"}),
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 10,
                "total_tokens": 20,
            },
        }
    if payload["messages"][-1].get("tool_call_id") is not None:
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
                            f"Mock response to: {payload["messages"][-1]["content"]}"
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
                        f"Mock response to: {payload}"
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
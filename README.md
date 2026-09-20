# mock-llm

A lightweight, OpenAI-compatible mock LLM server for local development, integration testing, and CI.

`mock-llm` provides a simple `/v1/chat/completions` endpoint that accepts OpenAI-style chat completion requests and returns deterministic mock responses. It is useful when you want to test an application without making requests to a real LLM provider.

## Why?

Testing LLM-powered applications can be difficult when real models introduce:

* API costs
* Network dependencies
* Slow responses
* Non-deterministic output
* Provider rate limits
* Unnecessary credentials in local or CI environments

`mock-llm` replaces the real model with a small local HTTP service that behaves like an OpenAI-compatible chat completion API.

## Features

* OpenAI-compatible chat completions endpoint
* Deterministic responses
* Supports arbitrary model names
* Simple FastAPI implementation
* No API key required
* Useful for local development and CI
* Lightweight and easy to run with Docker
* Returns mock token usage information

## API

### `POST /v1/chat/completions`

Example request:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {
        "role": "user",
        "content": "Hello, world!"
      }
    ]
  }'
```

Example response:

```json
{
  "id": "mock-chatcmpl-123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "[gpt-4o-mini] Mock response to: ..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 10,
    "total_tokens": 20
  }
}
```

The response includes the requested model name, making it useful for testing applications that dynamically configure or switch models.

## Getting Started

### Requirements

* Python 3.10+
* pip

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run locally

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

The server will be available at:

```text
http://localhost:8000
```

### Interactive API documentation

FastAPI automatically provides API documentation at:

```text
http://localhost:8000/docs
```

## Using with an OpenAI-compatible client

The server can be used as the base URL for an OpenAI-compatible SDK.

For example, with Python:

```python
from openai import OpenAI

client = OpenAI(
    api_key="mock-key",
    base_url="http://localhost:8000/v1",
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
)

print(response.choices[0].message.content)
```

No real API request is made.

## Docker

Build the image:

```bash
docker build -t mock-llm .
```

Run it:

```bash
docker run --rm -p 8000:8000 mock-llm
```

You can then use:

```text
http://localhost:8000/v1
```

as the OpenAI-compatible base URL.

## Docker Compose

If you prefer Docker Compose:

```bash
docker compose up --build
```

The service can then be accessed on the configured port.

## Use Cases

`mock-llm` is particularly useful for:

* Unit and integration tests
* CI/CD pipelines
* Local application development
* Testing OpenAI SDK integrations
* Testing error-handling logic
* Testing model selection logic
* Development without API credentials
* Avoiding LLM API costs during automated tests

## Limitations

This project intentionally keeps the implementation simple. It currently focuses on the basic OpenAI chat-completions request/response flow rather than reproducing the full behavior of a production LLM provider.

It should therefore be treated as a testing and development utility, not as an actual language model or production LLM gateway.

## Project Structure

```text
mock-llm/
├── app.py
├── Dockerfile
├── compose.yml
├── requirements.txt
└── .github/
    └── workflows/
```

## Contributing

Contributions, bug reports, and improvements are welcome.

If you find an issue or have an idea for improving the mock API, open an issue or submit a pull request.

## License

See the repository for license information.

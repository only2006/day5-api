import json

import httpx

url = "http://127.0.0.1:8000/chat/stream"
body = {
    "messages": [{"role": "user", "content": "用三句话介绍 Python"}],
    "max_tokens": 300,
}

with httpx.stream("POST", url, json=body, timeout=60.0) as response:
    response.raise_for_status()
    for line in response.iter_lines():
        if not line.startswith("data: "):
            continue
        payload = line.removeprefix("data: ").strip()
        if payload == "[DONE]":
            print("\n\n[流结束]")
            break
        data = json.loads(payload)
        if "delta" in data:
            print(data["delta"], end="", flush=True)
        elif "error" in data:
            print(f"\n[错误] {data['error']}")
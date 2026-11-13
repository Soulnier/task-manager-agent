"""Приблизительный размер сериализованного входа; фактический usage даёт API."""
import json


def packed(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def estimate(messages, tools=None):
    payload = {"messages": messages}
    if tools:
        payload["tools"] = tools
    return (len(packed(payload)) + 3) // 4

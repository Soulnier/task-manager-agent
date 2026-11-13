"""Воспроизводимое сравнение стратегий: из корня python -m agent.experiment [--live]."""
import argparse
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import httpx
from openai import OpenAI

from . import agent as app
from .context import estimate

QUESTION = ("Найди в документации приоритет по умолчанию, добавь отдельно задачи "
            "«Проверить отчёт» и «Подготовить защиту» с этим приоритетом, "
            "затем покажи незавершённые задачи.")
CALLS = [
    ("search_docs", {"query": "приоритет по умолчанию", "limit": 1}),
    ("add_task", {"title": "Проверить отчёт", "priority": "mid"}),
    ("add_task", {"title": "Подготовить защиту", "priority": "mid"}),
    ("list_tasks", {"status": "todo"}),
]


def fixture():
    step = 0

    def respond(request):
        nonlocal step
        data = json.loads(request.content)
        message = {"role": "assistant"}
        reason = "stop"
        if not data.get("tools"):
            message["content"] = "Тимур готовит защиту лабораторной."
        elif step < len(CALLS):
            name, args = CALLS[step]
            step += 1
            message["tool_calls"] = [{"id": f"call{step}", "type": "function",
                                      "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)}}]
            reason = "tool_calls"
        else:
            message["content"] = "Сценарий тестового сервера завершён."
        return httpx.Response(200, json={"id": "offline", "created": 0, "object": "chat.completion",
            "model": "offline-fixture", "choices": [{"index": 0, "finish_reason": reason, "message": message}]})
    return httpx.MockTransport(respond)


def history():
    return [{"role": "system", "content": app.SYSTEM_PROMPT},
            {"role": "user", "content": "Меня зовут Тимур. Моя цель — подготовить защиту."},
            {"role": "assistant", "content": "План подготовки. " * 220},
            {"role": "user", "content": QUESTION}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--budget", type=int)
    args = parser.parse_args()
    budget = args.budget or estimate(history(), app.TOOLS) + 310
    for strategy in ("trim", "summarize"):
        print(f"\n=== {strategy}, режим={'API' if args.live else 'локальный сценарий'}, бюджет={budget} ===")
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            shutil.copytree(app.AGENT_DIR / "workspace/docs", workspace / "docs")
            if args.live:
                key = app.os.getenv("OPENROUTER_API_KEY")
                if not key:
                    parser.exit(2, "Для --live заполните agent/.env.\n")
                client = OpenAI(api_key=key, base_url=app.os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                                timeout=60, max_retries=0)
                model = app.os.getenv("MODEL", "openrouter/free")
            else:
                client = OpenAI(api_key="offline", base_url="http://fixture.invalid/v1",
                                http_client=httpx.Client(transport=fixture()))
                model = "offline-fixture"
            with client, patch.object(app, "WORKSPACE", workspace):
                if args.live:
                    print(app.run_agent(client, model, history(), budget=budget, strategy=strategy))
                else:
                    with patch("builtins.input", return_value="y"):
                        print(app.run_agent(client, model, history(), budget=budget, strategy=strategy))


if __name__ == "__main__":
    main()

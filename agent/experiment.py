"""Воспроизводимое сравнение стратегий: из корня python -m agent.experiment [--live]."""
import argparse
import json
import shutil
import tempfile
import sys
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from openai import OpenAI, OpenAIError

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


def fixture(httpx):
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
    parser.add_argument("--log", type=Path, help="Путь к новому файлу журнала")
    args = parser.parse_args()
    if args.budget is not None and args.budget < 1:
        parser.error("--budget должен быть положительным")
    mode = "live" if args.live else "offline"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = args.log or app.AGENT_DIR / f"experiment-{mode}-{stamp}.txt"
    print(f"Журнал: {path.resolve()}", flush=True)
    try:
        log = path.open("x", encoding="utf-8-sig")
    except OSError as error:
        parser.exit(1, f"Не удалось создать журнал: {error}\n")
    with log, redirect_stdout(ConsoleLog(sys.stdout, log)):
        run_experiment(args, parser)


class ConsoleLog:
    """Дублирует вывод Python до кодирования консолью; stdin остаётся интерактивным."""

    def __init__(self, console, log):
        self.console = console
        self.log = log

    def write(self, text):
        self.log.write(text)
        self.console.write(text)
        self.flush()
        return len(text)

    def flush(self):
        self.log.flush()
        self.console.flush()


def run_experiment(args, parser):
    seed = history()
    baseline = estimate(seed, app.TOOLS)
    budget = args.budget or (6000 if args.live else baseline + 310)
    # В живом режиме оставляем место для более длинных результатов модели.
    # Чтобы сокращение всё же сработало, удлиняем только СТАРЫЙ учебный ход.
    if args.live:
        pad = max(0, (budget - 310 - baseline) * 4)
        phrase = "План подготовки. "
        seed[2]["content"] += (phrase * (pad // len(phrase) + 1))[:pad]
    failed = []
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
                try:
                    import httpx2 as httpx
                except ImportError:
                    import httpx
                client = OpenAI(api_key="offline", base_url="http://fixture.invalid/v1",
                                http_client=httpx.Client(transport=fixture(httpx)))
                model = "offline-fixture"
            with client, patch.object(app, "WORKSPACE", workspace):
                messages = [m.copy() for m in seed]
                try:
                    if args.live:
                        result = app.run_agent(client, model, messages, budget=budget, strategy=strategy)
                    else:
                        with patch("builtins.input", return_value="y"):
                            result = app.run_agent(client, model, messages, budget=budget, strategy=strategy)
                    print(result)
                except (ValueError, OpenAIError) as error:
                    failed.append(strategy)
                    print(f"Прогон {strategy} остановлен: {error}")
                    print(f"Оценка на момент ошибки: {estimate(messages, app.TOOLS)}; бюджет: {budget}.")
    if failed:
        print("Не завершились стратегии: " + ", ".join(failed))
        raise SystemExit(1)


if __name__ == "__main__":
    main()

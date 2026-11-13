"""Приблизительный размер сериализованного входа; фактический usage даёт API."""
import json


def packed(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def estimate(messages, tools=None):
    payload = {"messages": messages}
    if tools:
        payload["tools"] = tools
    return (len(packed(payload)) + 3) // 4


def ensure_context_budget(messages, tools, budget):
    """Вернуть окно, сохранив system и весь текущий ход (включая tool_calls)."""
    view = list(messages)
    before = estimate(view, tools)
    if before <= budget:
        return view
    turns = [i for i, m in enumerate(view) if m["role"] == "user"]
    for start in turns[1:]:
        kept = [messages[0], *messages[start:]]
        if estimate(kept, tools) <= budget:
            print(f"TRIM: removed={start-1} before={before} after={estimate(kept, tools)}")
            return kept
    raise ValueError("Текущий ход вместе с system и tools превышает бюджет. "
                     "Увеличьте CONTEXT_BUDGET или сократите запрос/данные.")

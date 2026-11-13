"""Приблизительный размер сериализованного входа; фактический usage даёт API."""
import json


def packed(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def estimate(messages, tools=None):
    payload = {"messages": messages}
    if tools:
        payload["tools"] = tools
    return (len(packed(payload)) + 3) // 4


def ensure_context_budget(messages, tools, budget, summarize=None):
    """Вернуть окно, сохранив system и весь текущий ход (включая tool_calls)."""
    view = list(messages)
    before = estimate(view, tools)
    if before <= budget:
        return view
    turns = [i for i, m in enumerate(view) if m["role"] == "user"]
    for start in turns[1:]:
        kept = [messages[0], *messages[start:]]
        if estimate(kept, tools) <= budget:
            if summarize:
                # Если есть ещё старые ходы, освободим место для самой памяти.
                if start != turns[-1] and budget - estimate(kept, tools) < min(180, budget // 5):
                    continue
                try:
                    note = summarize(messages[1:start]).strip()[:1200]
                    while note:
                        memory = {"role": "assistant", "content": "[память диалога] " + note}
                        candidate = [kept[0], memory, *kept[1:]]
                        excess = estimate(candidate, tools) - budget
                        if excess <= 0:
                            print(f"SUMMARY: removed={start-1} before={before} after={estimate(candidate, tools)}")
                            return candidate
                        note = note[:-max(1, 4 * excess)]
                    print("SUMMARY: нет места или пустой ответ; переход к trim.")
                except (ValueError, RuntimeError) as error:
                    print(f"SUMMARY: {error}; переход к trim.")
            print(f"TRIM: removed={start-1} before={before} after={estimate(kept, tools)}")
            return kept
    raise ValueError("Текущий ход вместе с system и tools превышает бюджет. "
                     "Увеличьте CONTEXT_BUDGET или сократите запрос/данные.")

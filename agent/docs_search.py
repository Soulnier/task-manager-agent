"""Поиск по абзацам локальной документации без внешнего индекса."""
import re


def words(text):
    return {w for w in re.findall(r"\w+", text.casefold()) if len(w) > 1}


def search(workspace, query, limit=3):
    if not isinstance(query, str) or not words(query):
        raise ValueError("Нужен непустой поисковый запрос.")
    if type(limit) is not int or not 1 <= limit <= 5:
        raise ValueError("limit должен быть целым числом от 1 до 5.")
    workspace = workspace.resolve()
    docs = workspace / "docs"
    if docs.resolve() != docs or not docs.is_dir():
        raise ValueError("Отсутствует локальный каталог workspace/docs.")
    terms = words(query)
    hits = []
    for file in sorted(docs.rglob("*")):
        if file.suffix.lower() not in (".txt", ".md") or not file.resolve().is_relative_to(docs):
            continue
        if not file.is_file() or file.stat().st_size > 50000:
            continue
        try:
            data = file.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        matched = []
        for idx, paragraph in enumerate(re.split(r"\n\s*\n", data)):
            score = len(terms & words(paragraph))
            if score:
                matched.append((-score, idx, " ".join(paragraph.split())[:360]))
        if matched:
            matched.sort()
            hits.append((matched[0][0], file.relative_to(workspace).as_posix(),
                         [part for _, _, part in matched[:3]]))
    hits.sort()
    return "\n\n".join(path + ":\n" + "\n".join(parts) for _, path, parts in hits[:limit]) or "Совпадений нет."

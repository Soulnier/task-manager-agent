import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


# Ищем .env рядом с agent.py независимо от папки запуска.
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)


def main():
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    base_url = os.getenv(
        "OPENROUTER_BASE_URL",
        "https://openrouter.ai/api/v1",
    )
    model = os.getenv("MODEL", "openrouter/free")

    if not api_key:
        print("Ошибка: укажи OPENROUTER_API_KEY в agent/.env.")
        return

    # Пакет openai отправляет запросы на сервер OpenRouter.
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=60.0,
        max_retries=0,
    )

    messages = [
        {
            "role": "system",
            "content": "Ты полезный помощник. Отвечай кратко на русском языке.",
        },
        {
            "role": "user",
            "content": "Объясни в двух предложениях, что такое ИИ-агент.",
        },
    ]

    print(f"Модель: {model}")
    print("Отправляем запрос...")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
    except OpenAIError as error:
        print(f"Ошибка обращения к модели: {error}")
        return
    finally:
        client.close()

    if not response.choices:
        print("Ошибка: модель не вернула вариантов ответа.")
        return

    choice = response.choices[0]

    print("\nmessage.content:")
    print(choice.message.content)

    print("\nfinish_reason:")
    print(choice.finish_reason)

    print("\nusage:")
    if response.usage is not None:
        print(response.usage.model_dump_json(indent=2))
    else:
        print("Провайдер не передал статистику токенов.")


def main():
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    base_url = os.getenv(
        "OPENROUTER_BASE_URL",
        "https://openrouter.ai/api/v1",
    )
    model = os.getenv("MODEL", "openrouter/free")

    if not api_key:
        print("Ошибка: укажи OPENROUTER_API_KEY в agent/.env.")
        return

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=60.0,
        max_retries=0,
    )

    # История создаётся один раз, до начала диалога.
    messages = [
        {
            "role": "system",
            "content": "Ты полезный помощник. Отвечай кратко на русском языке.",
        },
    ]

    print(f"Модель: {model}")
    print("Для завершения введи /exit.")

    try:
        while True:
            try:
                user_text = input("\nТы: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nДиалог завершён.")
                break

            if user_text.lower() == "/exit":
                print("Диалог завершён.")
                break

            if not user_text:
                continue

            messages.append({
                "role": "user",
                "content": user_text,
            })

            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                )
            except OpenAIError as error:
                # Убираем неудачный запрос из истории.
                messages.pop()
                print(f"Ошибка обращения к модели: {error}")
                continue

            if not response.choices:
                messages.pop()
                print("Ошибка: модель не вернула вариантов ответа.")
                continue

            choice = response.choices[0]
            answer = choice.message.content

            if not answer:
                messages.pop()
                print("Модель не вернула текст ответа. Повтори запрос.")
                continue

            messages.append({
                "role": "assistant",
                "content": answer,
            })

            print(f"\nАгент: {answer}")
            print(f"\nfinish_reason: {choice.finish_reason}")

            if response.usage is not None:
                usage = response.usage
                print(
                    f"Токены: вход={usage.prompt_tokens}, "
                    f"выход={usage.completion_tokens}, "
                    f"всего={usage.total_tokens}"
                )
            else:
                print("Статистика токенов отсутствует.")

    finally:
        client.close()


if __name__ == "__main__":
    main()
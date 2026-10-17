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


if __name__ == "__main__":
    main()
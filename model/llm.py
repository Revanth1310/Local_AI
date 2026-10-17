import requests
import time
import re
from datetime import datetime


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:4b"


def clean_qwen_response(text):
    """
    Remove Qwen reasoning blocks and return only
    the final visible answer.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove <think>...</think> blocks
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    # If an unmatched <think> appears, remove everything
    # from <think> onward.
    text = re.sub(
        r"<think>.*$",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    return text.strip()


def ask_qwen(
    prompt,
    think=False,
    num_predict=512
):
    start = time.perf_counter()

    print(
        f"START TIME: {datetime.now():%H:%M:%S}"
    )

    print(f"THINK: {think}")
    print(f"NUM_PREDICT: {num_predict}")

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "think": think,
        "options": {
            "num_predict": num_predict,
            "temperature": 0.7
        }
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=300
        )

        response.raise_for_status()

        data = response.json()

        raw_answer = data.get(
            "response",
            ""
        )

        answer = clean_qwen_response(
            raw_answer
        )

        if not answer:

            print(
                "WARNING: Ollama returned "
                "an empty final answer."
            )

            thinking = data.get(
                "thinking",
                ""
            )

            if thinking:
                print(
                    "Ollama returned thinking "
                    "but no visible answer."
                )

        end = time.perf_counter()

        print(
            f"END TIME:   {datetime.now():%H:%M:%S}"
        )

        print(
            f"RESPONSE TIME: "
            f"{end - start:.2f} seconds"
        )

        print(
            f"RAW RESPONSE LENGTH: "
            f"{len(raw_answer)}"
        )

        print(
            f"CLEAN RESPONSE LENGTH: "
            f"{len(answer)}"
        )

        return answer

    except requests.RequestException as error:

        print(
            f"Ollama request failed: {error}"
        )

        raise